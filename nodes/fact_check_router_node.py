from debate_state import DebateState
from langgraph.types import Command
from langgraph.graph import END
from configurations.debate_constants import (
    NODE_PRO_DEBATER,
    NODE_CON_DEBATER,
    NODE_DEBATE_MODERATOR,
    SPEAKER_CON,
    SPEAKER_PRO,
)

class FactCheckRouterNode:
    def __call__(self, state: DebateState) -> Command[str]:
        messages = state.get("messages", [])
        speaker = state.get("speaker")
        if not messages:
            raise ValueError("No messages found in the state.")
        last_message = messages[-1]
        pro_fact_checks = state.get("times_pro_fact_checked", 0)
        con_fact_checks = state.get("times_con_fact_checked", 0)

        if pro_fact_checks >= 3 or con_fact_checks >= 3:
            disqualified = SPEAKER_PRO if pro_fact_checks >= 3 else SPEAKER_CON
            winner = SPEAKER_CON if disqualified == SPEAKER_PRO else SPEAKER_PRO

            verdict_msg = {
                "speaker": "moderator",
                "content": (
                    f"Debate ended early due to excessive factual inaccuracies.\n\n"
                    f"DISQUALIFIED: {disqualified.upper()} (exceeded fact check limit)\n"
                    f"WINNER: {winner.upper()}"
                ),
                "validated": True,
                "stage": "verdict"
            }
            return Command(
                update={"messages": messages + [verdict_msg]},
                goto=END
            )
        if last_message.get("validated"):
            return Command(goto=NODE_DEBATE_MODERATOR)
        elif speaker == SPEAKER_PRO:
            return Command(goto=NODE_PRO_DEBATER)
        elif speaker == SPEAKER_CON:
            return Command(goto=NODE_CON_DEBATER)
        raise ValueError("Unable to determine routing in FactCheckRouterNode.")
