from debate_state import DebateMessage
from typing import List

def create_debate_message(speaker: str, content: str, stage: DebateMessage, validated: bool = False) -> DebateMessage:
    return DebateMessage(
        speaker=speaker,
        content=content,
        validated=validated,
        stage=stage
    )

def get_debate_history(messages: List[DebateMessage]) -> str:
    return "\n".join(
        f"[{msg['stage'].upper()}] {msg['speaker'].upper()}: {msg['content']}"
        for msg in messages
    )


