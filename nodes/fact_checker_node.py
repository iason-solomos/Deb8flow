from typing import Dict, Any
from openai import OpenAI
from debate_state import DebateState
from configurations.debate_constants import SPEAKER_PRO, SPEAKER_CON
import os
from utils import create_debate_message
from dotenv import load_dotenv
from pydantic import BaseModel, Field

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
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_GPT4O"))

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_message = messages[-1]
        claim = last_message["content"]
        speaker = last_message["speaker"]

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
        print(f"Fact-check result: {result}, Justification: {justification}")
        if result == "yes":
            # Mark the original message as validated
            last_message["validated"] = True
            return {
                "messages": messages,
                "validated": True
            }
        else:
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
