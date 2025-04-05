from nodes.base_component import BaseComponent
from debate_state import DebateState
from typing import Dict, Any
from configurations.debate_constants import (
    STAGE_REBUTTAL, STAGE_FINAL_ARGUMENT,
    SPEAKER_CON, SPEAKER_PRO
)
from prompts.con_debater_prompts import (
    SYSTEM_PROMPT,
    REBUTTAL_HUMAN_PROMPT,
    REBUTTAL_RETRY_HUMAN_PROMPT,
    FINAL_ARGUMENT_HUMAN_PROMPT,
    FINAL_ARGUMENT_RETRY_HUMAN_PROMPT,
)
from utils import create_debate_message, get_debate_history

class ConDebaterNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        self.rebuttal_chain = self.create_chain(SYSTEM_PROMPT, REBUTTAL_HUMAN_PROMPT)
        self.rebuttal_retry_chain = self.create_chain(SYSTEM_PROMPT, REBUTTAL_RETRY_HUMAN_PROMPT)
        self.final_argument_chain = self.create_chain(SYSTEM_PROMPT, FINAL_ARGUMENT_HUMAN_PROMPT)
        self.final_argument_retry_chain = self.create_chain(SYSTEM_PROMPT, FINAL_ARGUMENT_RETRY_HUMAN_PROMPT)

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)
        debate_topic = state["debate_topic"]
        messages = state.get("messages", [])
        stage = state["stage"]
        speaker = state["speaker"]

        # Determine if the CON agent is retrying due to a failed fact check
        last_msg = messages[-1] if messages else None
        retrying = last_msg and last_msg["speaker"] == SPEAKER_CON and not last_msg["validated"]

        if stage == STAGE_REBUTTAL and speaker == SPEAKER_CON:
            opponent_msg = self._get_last_message_by(SPEAKER_PRO, messages)
            chain = self.rebuttal_retry_chain if retrying else self.rebuttal_chain
            result = chain.invoke({
                "debate_topic": debate_topic,
                "opponent_statement": opponent_msg
            })

        elif stage == STAGE_FINAL_ARGUMENT and speaker == SPEAKER_CON:
            debate_history = get_debate_history(messages)
            chain = self.final_argument_retry_chain if retrying else self.final_argument_chain
            result = chain.invoke({
                "debate_topic": debate_topic,
                "debate_history": debate_history
            })

        else:
            raise ValueError(f"Unknown turn for ConDebater: stage={stage}, speaker={speaker}")

        new_message = create_debate_message(speaker=SPEAKER_CON, content=result, stage=stage)
        print(f"Speaker: {speaker}, Stage: {stage}, Retry: {retrying}\nMessage:\n{result}")
        return {
            "messages": messages + [new_message]
        }

    def _get_last_message_by(self, speaker: str, messages: list) -> str:
        for m in reversed(messages):
            if m["speaker"] == speaker:
                return m["content"]
        return ""
