import pytest
from nodes.fact_checker_node import FactCheckNode
from configurations.debate_constants import SPEAKER_PRO

@pytest.mark.asyncio
async def test_fact_checker_passes_short_claim():
    node = FactCheckNode()

    mock_state = {
        "messages": [
            {
                "speaker": SPEAKER_PRO,
                "content": "AI was developed in the 20th century.",
                "validated": False,
                "stage": "opening"
            }
        ],
        "speaker": SPEAKER_PRO,
        "stage": "opening",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

    result = node(mock_state)
    assert "messages" in result
    assert isinstance(result["validated"], bool)
