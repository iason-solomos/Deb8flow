from typing import Dict
from langchain_core.runnables.base import RunnableSequence
from nodes.base_component import BaseComponent
from debate_state import DebateState
from prompts.topic_generator_prompts import SYSTEM_PROMPT, HUMAN_PROMPT


class GenerateTopicNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        # Create the prompt chain.
        self.chain: RunnableSequence = self.create_chain(
            system_template=SYSTEM_PROMPT,
            human_template=HUMAN_PROMPT
        )

    def __call__(self, state: DebateState) -> Dict[str, str]:
        """
        Generates a debate topic and assigns positions to the two debaters.
        """
        super().__call__(state)

        topic_text = self.execute_chain({})

        # Store the topic and assign stances in the DebateState
        debate_topic = topic_text.strip()
        positions = {
            "pro": "In favor of the topic",
            "con": "Against the topic"
        }

        
        first_speaker = "pro"
        # self.logger.info("Welcome to our debate panel! Today's debate topic is: %s", debate_topic)

        self.logger.info("[bold green]┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓[/]")
        self.logger.info("[bold green]┃        DEBATE SESSION STARTED        ┃[/]")
        self.logger.info("[bold green]┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛[/]")
        self.logger.info("")
        self.logger.info("🏛️  [bold]Topic:[/] %s", topic_text.strip())
        self.logger.info("👥 [bold]Positions:[/]")
        self.logger.info("   ▸ [cyan]PRO:[/] In favor of the topic")
        self.logger.info("   ▸ [magenta]CON:[/] Against the topic")

        return {
            "debate_topic": debate_topic,
            "positions": positions,
            "stage": "opening",
            "speaker": first_speaker
        }
