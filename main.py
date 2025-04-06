import asyncio
from workflow.debate_workflow import DebateWorkflow
import os
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

def validate_env():
    required_var = "OPENAI_API_KEY_GPT4O"
    if not os.getenv(required_var):
        raise EnvironmentError(f"Missing environment variable: {required_var}")

async def main():
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")
    try:
        logger.info("Starting debate workflow...")
        workflow = DebateWorkflow()
        workflow_result = await workflow.run()
        
        final_message = workflow_result["messages"][-1]["content"]
        logger.info("\n\n=== DEBATE VERDICT ===\n%s\n====================", final_message)
        logger.info("Workflow completed successfully | Status: %s", "SUCCESS")
        
    except Exception as e:
        logger.error("Workflow failed: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())