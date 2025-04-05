import asyncio
from workflow.debate_workflow import DebateWorkflow

async def main():
    workflow = DebateWorkflow()
    workflow_result = await workflow.run()
    print(workflow_result["messages"][-1]["content"])
    print("Workflow completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())