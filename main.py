import asyncio
from workflow.debate_workflow import DebateWorkflow
import os

def validate_env():
    required_var = "OPENAI_API_KEY_GPT4O"
    if not os.getenv(required_var):
        raise EnvironmentError(f"Missing environment variable: {required_var}")

async def main():
    validate_env()
    workflow = DebateWorkflow()
    workflow_result = await workflow.run()
    print(workflow_result["messages"][-1]["content"])
    print("Workflow completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())