"""
CLI entry point for the IT Support Agent.
Starts the Flask admin panel and runs the AI agent to complete IT tasks.

Usage:
    python run_agent.py "Create a new user John Doe with email john@company.com in Engineering"
    python run_agent.py --interactive
    python run_agent.py --demo
"""

import sys
import os
import asyncio
import threading
import time
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def start_admin_panel(port=5000):
    """Start the Flask admin panel in a background thread."""
    from admin_panel.app import create_app
    app = create_app()

    # Run Flask in a daemon thread so it doesn't block
    def run():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import urllib.request
    for i in range(30):
        try:
            urllib.request.urlopen(f'http://localhost:{port}/')
            print(f"✅ Admin panel running at http://localhost:{port}")
            return True
        except Exception:
            time.sleep(0.5)

    print("❌ Failed to start admin panel")
    return False


async def run_task(task: str, headless: bool = False):
    """Run a single IT support task."""
    from agent.it_agent import ITSupportAgent
    agent = ITSupportAgent(admin_url="http://localhost:5000", headless=headless)
    result = await agent.execute_task(task)
    return result


async def interactive_mode(headless: bool = False):
    """Interactive mode: continuously accept and execute tasks."""
    from agent.it_agent import ITSupportAgent
    agent = ITSupportAgent(admin_url="http://localhost:5000", headless=headless)

    print("\n" + "=" * 60)
    print("🤖 IT Support Agent — Interactive Mode")
    print("=" * 60)
    print("Type your IT support requests in natural language.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            task = input("📋 Enter IT task: ").strip()
            if task.lower() in ('quit', 'exit', 'q'):
                print("\n👋 Goodbye!")
                break
            if not task:
                continue

            result = await agent.execute_task(task)

            if result['success']:
                print(f"\n✅ Success: {result['result']}\n")
            else:
                print(f"\n❌ Failed: {result['result']}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


async def demo_mode(headless: bool = False):
    """Run demo with predefined tasks to showcase capabilities."""
    from agent.it_agent import ITSupportAgent
    agent = ITSupportAgent(admin_url="http://localhost:5000", headless=headless)

    demo_tasks = [
        # Task 1: Create a new user
        "Create a new user named Alice Johnson with email alice.johnson@company.com in the Marketing department with the role Marketing Analyst and a Pro license",

        # Task 2: Reset password
        "Reset the password for sarah.johnson@company.com",

        # Task 3 (Bonus): Multi-step conditional
        "Check if bob.thompson@company.com exists and is active. If the user exists, change their license from Pro to Enterprise.",
    ]

    print("\n" + "=" * 60)
    print("🎬 IT Support Agent — Demo Mode")
    print(f"Running {len(demo_tasks)} demo tasks...")
    print("=" * 60)

    results = []
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n{'─' * 60}")
        print(f"📋 Demo Task {i}/{len(demo_tasks)}")
        print(f"{'─' * 60}")

        result = await agent.execute_task(task)
        results.append(result)

        if i < len(demo_tasks):
            print("\n⏳ Waiting 3 seconds before next task...\n")
            await asyncio.sleep(3)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Demo Results Summary")
    print("=" * 60)
    for i, r in enumerate(results, 1):
        status = "✅" if r['success'] else "❌"
        print(f"  {status} Task {i}: {r['task'][:60]}...")
        print(f"     Result: {r['result'][:100]}")
    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="IT Support AI Agent — Automate IT tasks using natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py "Create a new user John Doe with email john@company.com in Engineering"
  python run_agent.py "Reset password for sarah.johnson@company.com"
  python run_agent.py --interactive
  python run_agent.py --demo
  python run_agent.py --panel-only
        """
    )

    parser.add_argument('task', nargs='?', help='IT support task in natural language')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode (continuous task input)')
    parser.add_argument('--demo', '-d', action='store_true',
                        help='Run demo with predefined tasks')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no visible window)')
    parser.add_argument('--panel-only', action='store_true',
                        help='Only start the admin panel (no agent)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port for the admin panel (default: 5000)')

    args = parser.parse_args()

    # Validate API key
    if not args.panel_only and not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY environment variable not set.")
        print("   Create a .env file with: GOOGLE_API_KEY=your-key-here")
        sys.exit(1)

    # Start admin panel
    print("🚀 Starting IT Admin Panel...")
    if not start_admin_panel(port=args.port):
        sys.exit(1)

    if args.panel_only:
        print(f"\n🌐 Admin panel running at http://localhost:{args.port}")
        print("   Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopped.")
        return

    if args.demo:
        asyncio.run(demo_mode(headless=args.headless))
    elif args.interactive:
        asyncio.run(interactive_mode(headless=args.headless))
    elif args.task:
        result = asyncio.run(run_task(args.task, headless=args.headless))
        sys.exit(0 if result['success'] else 1)
    else:
        parser.print_help()
        print("\n💡 Try: python run_agent.py --demo")


if __name__ == '__main__':
    main()
