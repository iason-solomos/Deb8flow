"""
This module defines the BaseComponent class, which provides a foundation
for managing LLM-based workflows with optional token tracking integrated into the state.
"""
import logging
import time
from typing import Optional, List, Type, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_community.callbacks.manager import get_openai_callback
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import get_tracer_provider
from debate_state import DebateState
from configurations.llm_config import LLMConfig, OpenAILLMConfig, AzureOpenAILLMConfig


class BaseComponent:
    """
    A foundational class for managing LLM-based workflows with token tracking.
    Can handle both Azure OpenAI (AzureChatOpenAI) and OpenAI (ChatOpenAI).
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        temperature: float = 0.0,
        max_retries: int = 5,
    ):
        """
        Initializes the BaseComponent with optional LLM configuration and temperature.

        Args:
            llm_config (Optional[LLMConfig]): Configuration for either Azure or OpenAI.
            temperature (float): Controls the randomness of LLM outputs. Defaults to 0.0.
            max_retries (int): How many times to retry on 429 errors.
        """
        logger = logging.getLogger(self.__class__.__name__)
        tracer = trace.get_tracer(__name__, tracer_provider=get_tracer_provider())

        self.logger = logger
        self.tracer = tracer
        self.llm: Optional[ChatOpenAI] = None
        self.output_parser: Optional[StrOutputParser] = None
        self.state: Optional[DebateState] = None
        self.prompt_template: Optional[ChatPromptTemplate] = None
        self.chain: Optional[RunnableSequence] = None
        self.documents: Optional[List] = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.max_retries = max_retries

        if llm_config is not None:
            self.llm = self._init_llm(llm_config, temperature)
            self.output_parser = StrOutputParser()

    def _init_llm(self, config: LLMConfig, temperature: float):
        """
        Initializes an LLM instance for either Azure OpenAI or standard OpenAI.
        """
        if isinstance(config, AzureOpenAILLMConfig):
            # If it's Azure, use the AzureChatOpenAI class
            return AzureChatOpenAI(
                deployment_name=config.deployment_name,
                azure_endpoint=config.azure_endpoint,
                openai_api_version=config.openai_api_version,
                openai_api_key=config.openai_api_key,
                temperature=temperature,
            )
        elif isinstance(config, OpenAILLMConfig):
            # If it's standard OpenAI, use the ChatOpenAI class
            return ChatOpenAI(
                model_name=config.model_name,
                openai_api_key=config.openai_api_key,
                temperature=temperature,
            )
        else:
            raise ValueError("Unsupported LLMConfig type.")

    def validate_initialization(self) -> None:
        """
        Ensures we have an LLM and an output parser.
        """
        if not self.llm:
            raise ValueError("LLM is not initialized. Ensure `llm_config` is provided.")
        if not self.output_parser:
            raise ValueError("Output parser is not initialized.")

    def execute_chain(self, inputs: Any) -> Any:
        """
        Executes the LLM chain, tracks token usage, and retries on 429 errors.
        """
        if not self.chain:
            raise ValueError("No chain is initialized for execution.")

        retry_wait = 1  # Initial wait time in seconds

        for attempt in range(self.max_retries):
            try:
                with get_openai_callback() as cb:
                    result = self.chain.invoke(inputs)
                    self.logger.info("Prompt Token usage: %s", cb.prompt_tokens)
                    self.logger.info("Completion Token usage: %s", cb.completion_tokens)
                    self.prompt_tokens = cb.prompt_tokens
                    self.completion_tokens = cb.completion_tokens

                return result

            except Exception as e:
                # If the error mentions 429, do exponential backoff and retry
                if "429" in str(e):
                    self.logger.warning(
                        f"Rate limit reached. Retrying in {retry_wait} seconds... "
                        f"(Attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(retry_wait)
                    retry_wait *= 2
                else:
                    self.logger.error(f"Unexpected error: {str(e)}")
                    raise e

        raise Exception("API request failed after maximum number of retries")

    def create_chain(
        self, system_template: str, human_template: str
    ) -> RunnableSequence:
        """
        Creates a chain for unstructured outputs.
        """
        self.validate_initialization()
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("human", human_template),
            ]
        )
        self.chain = self.prompt_template | self.llm | self.output_parser
        return self.chain

    def create_structured_output_chain(
        self, system_template: str, human_template: str, output_model: Type[BaseModel]
    ) -> RunnableSequence:
        """
        Creates a chain that yields structured outputs (parsed into a Pydantic model).
        """
        self.validate_initialization()
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                ("human", human_template),
            ]
        )
        self.chain = self.prompt_template | self.llm.with_structured_output(output_model)
        return self.chain

    def build_return_with_tokens(self, node_specific_data: dict) -> dict:
        """
        Convenience method to add token usage info into the return values.
        """
        return {
            **node_specific_data,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    def __call__(self, state: DebateState) -> None:
        """
        Updates the node's local copy of the state.
        """
        self.logger.info("Calling node %s", self.__class__.__name__)
        self.state = state
        for key, value in state.items():
            setattr(self, key, value)
