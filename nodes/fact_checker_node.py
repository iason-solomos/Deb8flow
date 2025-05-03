import textwrap
from typing import Dict, Any
from openai import OpenAI
from debate_state import DebateState
from configurations.debate_constants import SPEAKER_PRO, SPEAKER_CON
import os
from utils import create_debate_message
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging

load_dotenv()

class FactCheck(BaseModel):
    """
    Pydantic model for the fact checking the claims made by debaters.

    Attributes:
        binary_score (str): 'yes' if the claim is verifiable and truthful, 'no' otherwise.
    """

    binary_score: str = Field(
        description="Indicates if the claim is verifiable and truthful. 'yes' or 'no'."
    )
    justification: str = Field(
        description="Explanation of the reasoning behind the score."
    )

class FactCheckNode:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(self.__class__.__name__)
        self._configure_rich_logger() 


    def _configure_rich_logger(self):
        """Initialize rich logging for standalone nodes"""
        from rich.console import Console
        from rich.logging import RichHandler
        
        console = Console(width=100)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            markup=True,
            show_path=False
        )
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_message = messages[-1]
        claim = last_message["content"]
        speaker = last_message["speaker"]
        stage = state["stage"]

        self.logger.info(
        f"[bold red]Fact-Checking {speaker.upper()}'s {stage.title()} Claim:[/]\n"
        f"[dim]{textwrap.shorten(claim, width=150, placeholder='...')}[/]"
    )

        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-search-preview",
            web_search_options={},
            messages=[{
                "role": "user",
                "content": (
                        f"Consider the following statement from a debate. "
                        f"If the statement contains numbers, or figures from studies, fact-check it online.\n\n"
                        f"Statement:\n\"{claim}\"\n\n"
                        f"Reply clearly whether any numbers or studies might be inaccurate or hallucinated, and why."
                        f"\n"
                        f"If the statement doesn't contain references to studies or numbers cited, don't go online to fact-check, and just consider it successfully fact-checked, with a 'yes' score.\n\n"
                )
            }],
            response_format=FactCheck
        )


        result = completion.choices[0].message.parsed.binary_score
        justification = completion.choices[0].message.parsed.justification
        if result == "yes":
            self.logger.info(f"[green]✅ Verified[/]\n"f"[dim]{justification}[/]")
            last_message["validated"] = True
            return {
                "messages": messages,
                "validated": True
            }
        else:
            self.logger.info(f"[red]❌ Disputed[/]\n"f"[bold]Reason:[/] {justification}\n"f"[yellow]⚠ {speaker.upper()} now has {state.get(f'times_{speaker}_fact_checked', 0) + 1}/3 failed checks[/]")
            fact_checker_msg = create_debate_message(
                speaker="fact_checker",
                content=result,
                stage=state["stage"]
            )
            if speaker == SPEAKER_PRO:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_pro_fact_checked": state.get("times_pro_fact_checked", 0) + 1,
                }
            elif speaker == SPEAKER_CON:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_con_fact_checked": state.get("times_con_fact_checked", 0) + 1,
                }
