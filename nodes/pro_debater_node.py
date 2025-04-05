from nodes.base_component import BaseComponent
from debate_state import DebateState
from typing import Dict, Any
from prompts.pro_debater_prompts import (
    SYSTEM_PROMPT,
    OPENING_HUMAN_PROMPT,
    COUNTER_HUMAN_PROMPT,
    OPENING_RETRY_HUMAN_PROMPT,
    COUNTER_RETRY_HUMAN_PROMPT
)
from utils import create_debate_message, get_debate_history
from configurations.debate_constants import (
    STAGE_OPENING,
    STAGE_COUNTER,
    SPEAKER_PRO,
    SPEAKER_CON
)

class ProDebaterNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        self.opening_chain = self.create_chain(SYSTEM_PROMPT, OPENING_HUMAN_PROMPT)
        self.opening_retry_chain = self.create_chain(SYSTEM_PROMPT, OPENING_RETRY_HUMAN_PROMPT)
        self.counter_chain = self.create_chain(SYSTEM_PROMPT, COUNTER_HUMAN_PROMPT)
        self.counter_retry_chain = self.create_chain(SYSTEM_PROMPT, COUNTER_RETRY_HUMAN_PROMPT)

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)

        debate_topic = state.get("debate_topic")
        messages = state.get("messages", [])
        stage = state.get("stage")
        speaker = state.get("speaker")

        # Check if retrying (last message was by pro and not validated)
        last_msg = messages[-1] if messages else None
        retrying = last_msg and last_msg["speaker"] == SPEAKER_PRO and not last_msg["validated"]

        if stage == STAGE_OPENING and speaker == SPEAKER_PRO:
            chain = self.opening_retry_chain if retrying else self.opening_chain # select which chain we are triggering: the normal one or the fact-cehcked one
            result = chain.invoke({
                "debate_topic": debate_topic
            })
        elif stage == STAGE_COUNTER and speaker == SPEAKER_PRO:
            opponent_msg = self._get_last_message_by(SPEAKER_CON, messages)
            debate_history = get_debate_history(messages)
            chain = self.counter_retry_chain if retrying else self.counter_chain
            result = chain.invoke({
                "debate_topic": debate_topic,
                "opponent_statement": opponent_msg,
                "debate_history": debate_history
            })
        else:
            raise ValueError(f"Unknown turn for ProDebater: stage={stage}, speaker={speaker}")
        new_message = create_debate_message(speaker=SPEAKER_PRO, content=result, stage=stage)
        print(f"Speaker: {speaker}, Stage: {stage}, Retry: {retrying}\nMessage:\n{result}")
        return {
            "messages": messages + [new_message]
        }

    def _get_last_message_by(self, speaker_prefix, messages):
        for m in reversed(messages):
            if m.get("speaker") == speaker_prefix:
                return m["content"]
        return ""
