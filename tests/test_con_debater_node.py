import pytest
from nodes.con_debater_node import ConDebaterNode
from configurations.llm_config import llm_config_map
from configurations.debate_constants import STAGE_REBUTTAL, SPEAKER_CON

@pytest.mark.asyncio
async def test_con_rebuttal_statement():
    node = ConDebaterNode(llm_config_map["gpt-4o"], temperature=0.1)

    mock_state = {
        "debate_topic": "Should AI be used in hiring decisions?",
        "messages": [
            {
                "speaker": "pro",
                "content": "AI makes hiring more efficient and less biased.",
                "validated": True,
                "stage": "opening"
            }
        ],
        "stage": STAGE_REBUTTAL,
        "speaker": SPEAKER_CON,
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

    result = node(mock_state)
    assert "messages" in result
    assert result["messages"][-1]["speaker"] == "con"
    assert len(result["messages"][-1]["content"]) > 10
