"""
IT Support AI Agent using browser-use for browser automation.
Takes natural-language IT support requests and executes them on the admin panel.
"""

import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.prompts import ADMIN_PANEL_SYSTEM_PROMPT

load_dotenv()


class ITSupportAgent:
    """
    AI agent that processes IT support requests by automating
    browser interactions with the IT Admin Panel.
    """

    def __init__(self, admin_url="http://localhost:5000", headless=False):
        self.admin_url = admin_url
        self.headless = headless
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )

    async def execute_task(self, task_description: str) -> dict:
        """
        Execute a natural-language IT support task using browser automation.

        Args:
            task_description: Natural language description of the IT task
                e.g., "Create a new user John Doe with email john@company.com in Engineering"

        Returns:
            dict with 'success' (bool), 'result' (str), and 'task' (str)
        """
        print(f"\n{'='*60}")
        print(f"🤖 IT Support Agent")
        print(f"{'='*60}")
        print(f"📋 Task: {task_description}")
        print(f"🌐 Admin Panel: {self.admin_url}")
        print(f"{'='*60}\n")

        # Build the full task prompt
        full_task = f"""Navigate to {self.admin_url} and complete this IT support request:

{task_description}

After completing the task, verify the result by checking for a success message or confirming the changes on the page.
Report what you did and the outcome."""

        browser = Browser(
            config=BrowserConfig(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
        )

        try:
            agent = Agent(
                task=full_task,
                llm=self.llm,
                browser=browser,
                extend_system_message=ADMIN_PANEL_SYSTEM_PROMPT,
            )

            result = await agent.run()

            # Extract the final result
            final_result = result.final_result() if result.final_result() else "Task completed (no explicit result returned)"

            print(f"\n{'='*60}")
            print(f"✅ Task completed")
            print(f"📝 Result: {final_result}")
            print(f"{'='*60}\n")

            return {
                'success': True,
                'result': final_result,
                'task': task_description
            }

        except Exception as e:
            error_msg = str(e)
            print(f"\n{'='*60}")
            print(f"❌ Task failed: {error_msg}")
            print(f"{'='*60}\n")

            return {
                'success': False,
                'result': f"Error: {error_msg}",
                'task': task_description
            }

        finally:
            await browser.close()

    async def execute_conditional_task(self, task_description: str) -> dict:
        """
        Execute a multi-step conditional task.
        The LLM naturally handles conditional logic through its reasoning.

        Example task: "Check if alice@company.com exists. If not, create her
        in Marketing department as a Marketing Analyst with a Pro license."

        This works because the browser-use agent's LLM can:
        1. Search for the user
        2. Observe whether they appear in results
        3. Decide on next steps based on what it sees
        """
        # Multi-step conditional tasks are handled by the same agent
        # The LLM's reasoning ability naturally handles if/then logic
        print(f"\n🔄 Executing conditional/multi-step task...")
        return await self.execute_task(task_description)


async def run_single_task(task: str, admin_url: str = "http://localhost:5000", headless: bool = False):
    """Convenience function to run a single task."""
    agent = ITSupportAgent(admin_url=admin_url, headless=headless)
    return await agent.execute_task(task)


async def run_demo():
    """Run a demo with sample IT tasks."""
    agent = ITSupportAgent()

    demo_tasks = [
        "Create a new user Alice Johnson with email alice.johnson@company.com in the Marketing department as a Marketing Analyst with a Pro license",
        "Reset the password for john.smith@company.com",
        "Check if alice.johnson@company.com exists. If she does, change her license to Enterprise. If she doesn't exist, create her in Marketing with a Pro license.",
    ]

    for task in demo_tasks:
        result = await agent.execute_task(task)
        print(f"\nResult: {result}\n")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
