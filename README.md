# 🤖 AI IT Support Agent

An AI agent that takes **natural-language IT support requests** (like "reset password for john@company.com" or "create a new user") and carries them out automatically on a mock IT admin panel using **browser automation** — no direct DOM selectors or API shortcuts.

The agent uses [browser-use](https://github.com/browser-use/browser-use) (Playwright + LLM) to navigate the admin panel exactly like a human would: clicking buttons, filling forms, reading page content, and making decisions.

---

## 🎬 Demo

The agent completing two IT tasks end-to-end:

1. **Create User**: "Create a new user Alice Johnson with email alice.johnson@company.com in Marketing as a Marketing Analyst with a Pro license"
2. **Reset Password**: "Reset password for sarah.johnson@company.com"
3. **Multi-step Conditional**: "Check if bob.thompson@company.com exists. If yes, change their license to Enterprise."

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Entry Points                            │
│                                                             │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   CLI    │  │  Webhook API │  │  Slack Slash Command  │  │
│  │run_agent │  │  POST /webhook│  │  POST /webhook/slack │  │
│  └────┬─────┘  └──────┬───────┘  └──────────┬────────────┘  │
│       │               │                     │               │
│       └───────────────┼─────────────────────┘               │
│                       ▼                                     │
│            ┌─────────────────────┐                          │
│            │   IT Support Agent  │                          │
│            │  (browser-use +     │                          │
│            │   Gemini 3.1 Pro)    │                          │
│            └──────────┬──────────┘                          │
│                       │ Browser Automation                  │
│                       │ (Playwright)                        │
│                       ▼                                     │
│            ┌─────────────────────┐                          │
│            │  Mock IT Admin      │                          │
│            │  Panel (Flask)      │                          │
│            │                     │                          │
│            │  • Dashboard        │                          │
│            │  • User Management  │──── SQLite DB            │
│            │  • Audit Logs       │                          │
│            └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **browser-use over Selenium/raw Playwright**: Instead of writing brittle CSS selectors, the agent uses vision + LLM reasoning to understand the page and interact naturally. This is resilient to UI changes.

2. **Flask with server-rendered HTML**: Keeps the admin panel simple and functional (as required). No SPA complexity — just standard forms and pages that are easy for the browser agent to navigate.

3. **System prompt engineering**: The agent receives a detailed description of the admin panel layout in its system prompt, enabling it to navigate efficiently without trial-and-error.

4. **Multi-step conditional logic**: The LLM naturally handles if/then logic — it searches for a user, observes the result, and decides what to do next.

## 📦 Final Delivery Instructions
Before submitting your assignment, don't forget to:
1. **Record your Loom video**: Run `python run_agent.py --demo` and narrate your architecture decisions while it executes.
2. **Push to GitHub**: Initialize a Git repository here, commit the code, and either make the repository public OR invite `getsarthakaggarwal@gmail.com` to your private repo.

---
## 🚀 Quick Start

### Prerequisites
- Python >= 3.11
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/it-support-agent.git
cd it-support-agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
playwright install chromium

# 5. Set your API key
copy .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key-here
```

### Usage

```bash
# Run a single task
python run_agent.py "Create a new user John Doe with email john@company.com in Engineering"

# Reset a password
python run_agent.py "Reset password for sarah.johnson@company.com"

# Multi-step conditional task (bonus)
python run_agent.py "Check if alice@company.com exists. If not, create her in Marketing with Pro license"

# Interactive mode (keep entering tasks)
python run_agent.py --interactive

# Demo mode (runs 3 predefined tasks)
python run_agent.py --demo

# Just start the admin panel (browse manually)
python run_agent.py --panel-only

# Headless mode (no visible browser)
python run_agent.py --headless "Reset password for john.smith@company.com"
```

---

## 🔗 Webhook / Slack Integration (Bonus)

### Start the webhook server

```bash
python -m webhook.server
```

This starts both the admin panel (port 5000) and webhook API (port 5001).

### Direct HTTP trigger

```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{"task": "Reset password for john.smith@company.com"}'
```

### Async mode (fire-and-forget)

```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{"task": "Create user Jane in Sales", "async": true}'

# Check results later
curl http://localhost:5001/webhook/history
```

### Slack Slash Command

1. Create a Slack app at [api.slack.com](https://api.slack.com)
2. Add a Slash Command (e.g., `/it-support`)
3. Set the Request URL to `https://your-server:5001/webhook/slack`
4. Use it: `/it-support reset password for john@company.com`

---

## 🐳 Docker Deployment (Bonus)

```bash
# Build and run
docker-compose up --build

# Or build manually
docker build -t it-support-agent .
docker run -p 5000:5000 -p 5001:5001 -e OPENAI_API_KEY=your-key it-support-agent
```

---

## 📋 Supported Tasks

| Task | Example |
|---|---|
| Create User | "Create a new user John Doe with email john@company.com in Engineering" |
| Reset Password | "Reset password for john@company.com" |
| Delete User | "Remove the user sarah@company.com" |
| Edit User | "Change john@company.com's department to Marketing" |
| Assign License | "Assign Enterprise license to john@company.com" |
| Deactivate User | "Deactivate bob@company.com's account" |
| Activate User | "Re-activate lisa.anderson@company.com" |
| Check User | "Check if alice@company.com exists and what their status is" |
| Conditional | "If john@company.com exists, reset their password. If not, create them in Engineering" |

---

## 🗂️ Project Structure

```
it-support-agent/
├── README.md               # This file
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose config
├── run_agent.py            # CLI entry point
├── admin_panel/            # Mock IT Admin Panel (Flask)
│   ├── app.py              # Flask routes & app factory
│   ├── models.py           # SQLAlchemy models + seed data
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html       # Base layout with sidebar
│       ├── dashboard.html  # Dashboard with stats
│       ├── users.html      # User list with actions
│       ├── user_form.html  # Create/Edit user form
│       └── logs.html       # Audit log viewer
├── agent/                  # AI Browser Agent
│   ├── it_agent.py         # browser-use agent logic
│   └── prompts.py          # LLM system prompts
└── webhook/                # Webhook/Slack Integration
    └── server.py           # HTTP webhook endpoints
```

---

## ⚙️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Admin Panel | Flask + Jinja2 | Server-rendered IT admin UI |
| Database | SQLite + SQLAlchemy | User & audit log storage |
| AI Agent | browser-use | LLM-driven browser automation |
| LLM | OpenAI GPT-4o | Reasoning & decision-making |
| Browser Engine | Playwright (Chromium) | Actual browser control |
| Webhook API | Flask | HTTP/Slack trigger endpoint |
| Deployment | Docker + Compose | Containerized deployment |

---

## 📝 License

MIT
