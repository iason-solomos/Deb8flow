from nodes.base_component import BaseComponent
from prompts.judge_prompts import JUDGE_SYSTEM_PROMPT, JUDGE_HUMAN_PROMPT
from utils import get_debate_history
from configurations.debate_constants import SPEAKER_JUDGE
from debate_state import DebateState
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

class DebateVerdict(BaseModel):
    """
    Judgment of a debate based on rhetorical performance.

    Attributes:
        winner (Literal): Either 'pro' or 'con', indicating who performed better overall.
        justification (str): The reason for the judgment, focusing on rhetorical skill, clarity, and structure.
    """

    winner: Literal["pro", "con"] = Field(
        description="Indicates the winner of the debate. Must be 'pro' or 'con'."
    )
    justification: str = Field(
        description="A concise explanation of why this speaker won. Focus on rhetorical quality, not correctness of stance."
    )

class JudgeNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.3):
        super().__init__(llm_config, temperature)
        self.chain = self.create_structured_output_chain(JUDGE_SYSTEM_PROMPT, JUDGE_HUMAN_PROMPT, DebateVerdict)

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)

        debate_topic = state.get("debate_topic")
        messages = state.get("messages", [])
        debate_history = get_debate_history(messages)

        result = self.chain.invoke({
            "debate_topic": debate_topic,
            "debate_history": debate_history
        })

        return {
            "judge_verdict": result.dict(),
            "messages": messages + [{
                "speaker": SPEAKER_JUDGE,
                "content": f"WINNER: {result.winner.upper()}\n\nREASON: {result.justification}",
                "validated": True,
                "stage": "verdict"
            }]
        }
