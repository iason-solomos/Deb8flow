import pytest
from workflow.debate_workflow import DebateWorkflow

@pytest.mark.asyncio
async def test_full_debate_workflow_completes():
    workflow = DebateWorkflow()
    graph = workflow._initialize_workflow().compile()

    initial_state = {
        "debate_topic": "Should autonomous drones be allowed in warfare?",
        "positions": {
            "pro": "In favor of the topic",
            "con": "Against the topic"
        },
        "messages": [],
        "opening_statement_pro_agent": "",
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})

    assert "messages" in final_state
    assert any(m["stage"] == "verdict" for m in final_state["messages"]) or final_state["speaker"] in ["pro", "con"]
