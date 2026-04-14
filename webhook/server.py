"""
Webhook server for triggering IT Support Agent via HTTP/Slack.

This provides an HTTP endpoint that accepts IT support requests from:
1. Direct HTTP POST requests (any client)
2. Slack slash commands or outgoing webhooks
3. MS Teams incoming webhooks

Usage:
    python -m webhook.server

Endpoints:
    POST /webhook          — Direct HTTP trigger
    POST /webhook/slack    — Slack-formatted trigger
    GET  /webhook/health   — Health check
    GET  /webhook/history  — Recent task history
"""

import sys
import os
import asyncio
import json
import threading
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

webhook_app = Flask(__name__)

# In-memory task history
task_history = []


def start_admin_panel(port=5002):
    """Start the admin panel in a background thread."""
    from admin_panel.app import create_app
    app = create_app()

    def run():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://localhost:{port}/')
            return True
        except Exception:
            time.sleep(0.5)
    return False


def run_agent_task(task: str, headless: bool = True) -> dict:
    """Run an agent task in a new event loop."""
    from agent.it_agent import ITSupportAgent

    async def _run():
        admin_port = os.getenv('ADMIN_PORT', '5002')
        agent = ITSupportAgent(admin_url=f"http://localhost:{admin_port}", headless=headless)
        return await agent.execute_task(task)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@webhook_app.route('/webhook/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'IT Support Agent Webhook',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@webhook_app.route('/webhook', methods=['POST'])
def handle_webhook():
    """
    Handle direct HTTP webhook trigger.

    Expected JSON body:
    {
        "task": "Reset password for john@company.com",
        "async": false  // optional, default false
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    task = data.get('task', '').strip()

    if not task:
        return jsonify({'error': 'Missing "task" field in request body'}), 400

    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        return jsonify({'error': 'GOOGLE_API_KEY not configured'}), 500

    is_async = data.get('async', False)

    if is_async:
        # Run in background thread
        def _background():
            result = run_agent_task(task, headless=True)
            result['completed_at'] = datetime.now(timezone.utc).isoformat()
            task_history.append(result)

        thread = threading.Thread(target=_background, daemon=True)
        thread.start()

        return jsonify({
            'status': 'accepted',
            'message': f'Task queued: {task}',
            'note': 'Check /webhook/history for results'
        }), 202
    else:
        # Run synchronously
        result = run_agent_task(task, headless=True)
        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        task_history.append(result)

        return jsonify(result)


@webhook_app.route('/webhook/slack', methods=['POST'])
def handle_slack():
    """
    Handle Slack slash command or outgoing webhook.

    Slack sends form-encoded data with:
    - text: the command text
    - user_name: who sent it
    - channel_name: which channel

    Setup in Slack:
    1. Create a Slash Command (e.g., /it-support)
    2. Set Request URL to: https://your-server/webhook/slack
    """
    # Slack sends form data, not JSON
    task = request.form.get('text', '').strip()
    user_name = request.form.get('user_name', 'unknown')
    channel = request.form.get('channel_name', 'unknown')

    if not task:
        return jsonify({
            'response_type': 'ephemeral',
            'text': '❌ Please provide a task. Example: `/it-support reset password for john@company.com`'
        })

    # Respond immediately (Slack has a 3-second timeout)
    # Run the actual task in a background thread
    def _background():
        result = run_agent_task(task, headless=True)
        result['requested_by'] = user_name
        result['channel'] = channel
        result['completed_at'] = datetime.now(timezone.utc).isoformat()
        task_history.append(result)
        # In production, you'd send a follow-up message to Slack via response_url

    thread = threading.Thread(target=_background, daemon=True)
    thread.start()

    return jsonify({
        'response_type': 'in_channel',
        'text': f'🤖 IT Support Agent is working on: *{task}*\n_Requested by @{user_name} — results will be posted shortly._'
    })


@webhook_app.route('/webhook/history', methods=['GET'])
def get_history():
    """Get recent task history."""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'tasks': task_history[-limit:],
        'total': len(task_history)
    })


def main():
    """Start the webhook server along with the admin panel."""
    admin_port = int(os.getenv('ADMIN_PORT', 5002))
    webhook_port = int(os.getenv('PORT', os.getenv('WEBHOOK_PORT', 7860)))
    
    print(f"🚀 Starting IT Admin Panel on port {admin_port}...")
    if not start_admin_panel(admin_port):
        print("❌ Failed to start admin panel")
        sys.exit(1)
    print(f"✅ Admin panel running at http://localhost:{admin_port}")

    print(f"\n🔗 Webhook server starting on http://localhost:{webhook_port}")
    print(f"   (Running on Hugging Face? Use port 7860)")
    print(f"   POST /webhook          — Direct HTTP trigger")
    print(f"   POST /webhook/slack    — Slack slash command")
    print(f"   GET  /webhook/health   — Health check")
    print(f"   GET  /webhook/history  — Task history")
    print(f"\nExample:")
    print(f'   curl -X POST http://localhost:{webhook_port}/webhook \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"task": "Reset password for john.smith@company.com"}}\'')

    webhook_app.run(host='0.0.0.0', port=webhook_port, debug=False)


if __name__ == '__main__':
    main()
