from langgraph.types import Command
from typing import Literal
from debate_state import DebateState
from configurations.debate_constants import (
    STAGE_OPENING, STAGE_REBUTTAL, STAGE_COUNTER, STAGE_FINAL_ARGUMENT,
    SPEAKER_PRO, SPEAKER_CON,
    NODE_PRO_DEBATER, NODE_CON_DEBATER, NODE_JUDGE
)

class DebateModeratorNode:
    def __call__(self, state: DebateState) -> Command[Literal["pro_debater_node", "con_debater_node", "__end__"]]:
        stage = state["stage"]
        speaker = state["speaker"]

        if stage == STAGE_OPENING and speaker == SPEAKER_PRO:
            return Command(
                update={"stage": STAGE_REBUTTAL, "speaker": SPEAKER_CON},
                goto=NODE_CON_DEBATER
            )
        elif stage == STAGE_REBUTTAL and speaker == SPEAKER_CON:
            return Command(
                update={"stage": STAGE_COUNTER, "speaker": SPEAKER_PRO},
                goto=NODE_PRO_DEBATER
            )
        elif stage == STAGE_COUNTER and speaker == SPEAKER_PRO:
            return Command(
                update={"stage": STAGE_FINAL_ARGUMENT, "speaker": SPEAKER_CON},
                goto=NODE_CON_DEBATER
            )
        elif stage == STAGE_FINAL_ARGUMENT and speaker == SPEAKER_CON:
            return Command(
                update={},
                goto=NODE_JUDGE
            )

        raise ValueError(f"Unexpected stage/speaker combo: stage={stage}, speaker={speaker}")
