from langgraph.graph import StateGraph, END
from debate_state import DebateState
from nodes.topic_generator_node import GenerateTopicNode
from nodes.pro_debater_node import ProDebaterNode
from nodes.con_debater_node import ConDebaterNode
from nodes.debate_moderator_node import DebateModeratorNode
from nodes.fact_checker_node import FactCheckNode
from nodes.fact_check_router_node import FactCheckRouterNode
from nodes.judge_node import JudgeNode
from configurations.llm_config import llm_config_map

class DebateWorkflow:

    def _initialize_workflow(self) -> StateGraph:
        workflow = StateGraph(DebateState)
        # Nodes
        workflow.add_node("generate_topic_node", GenerateTopicNode(llm_config_map["gpt-4.1"]))
        workflow.add_node("pro_debater_node", ProDebaterNode(llm_config_map["gpt-4.1"]))
        workflow.add_node("con_debater_node", ConDebaterNode(llm_config_map["gpt-4.1"]))
        workflow.add_node("fact_check_node", FactCheckNode())
        workflow.add_node("fact_check_router_node", FactCheckRouterNode())
        workflow.add_node("debate_moderator_node", DebateModeratorNode())
        workflow.add_node("judge_node", JudgeNode(llm_config_map["gpt-4.1"]))

        # Entry point
        workflow.set_entry_point("generate_topic_node")

        # Flow
        workflow.add_edge("generate_topic_node", "pro_debater_node")
        workflow.add_edge("pro_debater_node", "fact_check_node")
        workflow.add_edge("con_debater_node", "fact_check_node")
        workflow.add_edge("fact_check_node", "fact_check_router_node")
        workflow.add_edge("judge_node", END)
        return workflow



    async def run(self):
        workflow = self._initialize_workflow()
        graph = workflow.compile()
        # graph.get_graph().draw_mermaid_png(output_file_path="workflow_graph.png")
        initial_state = {
            "topic": "",
            "positions": {}
        }
        final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
        return final_state
