# Bolna to Slack Integration

FastAPI service that triggers Bolna Voice AI calls and sends Slack notifications when calls end.

## Features

- **Make Calls** - Trigger real Bolna Voice AI calls via web interface
- **Simulate Calls** - Test Slack integration without using Bolna credits
- **Webhook Handler** - Receive call completion data from Bolna
- **Slack Alerts** - Send formatted notifications with call ID, agent ID, duration, and transcript

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env with your keys
python app.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `BOLNA_API_KEY` | Bolna API key |
| `BOLNA_AGENT_ID` | Agent ID (optional) |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/make-call` | POST | Trigger Bolna call |
| `/simulate-call` | POST | Simulate call |
| `/webhook/bolna` | POST | Receive webhook |
| `/health` | GET | Health check |
| `/docs` | GET | API docs |

## Deployment

Deployed on Render: https://bolna-slack-integration-btnu.onrender.com
