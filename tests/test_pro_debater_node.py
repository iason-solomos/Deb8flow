import pytest
from nodes.pro_debater_node import ProDebaterNode
from configurations.llm_config import llm_config_map
from configurations.debate_constants import STAGE_OPENING, SPEAKER_PRO

@pytest.mark.asyncio
async def test_pro_debater_opening_statement():
    node = ProDebaterNode(llm_config_map["gpt-4o"], temperature=0.1)

    mock_state = {
        "debate_topic": "Should governments ban facial recognition technology?",
        "messages": [],
        "stage": STAGE_OPENING,
        "speaker": SPEAKER_PRO
    }

    result = node(mock_state)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["speaker"] == "pro"
    assert result["messages"][0]["content"]
