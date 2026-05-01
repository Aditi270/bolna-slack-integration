"""
Bolna to Slack Integration
A FastAPI service that triggers Bolna Voice AI calls and sends Slack notifications when calls end.
"""

import os
import uuid
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
BOLNA_API_KEY = os.getenv("BOLNA_API_KEY")
BOLNA_AGENT_ID = os.getenv("BOLNA_AGENT_ID", "d311e737-70e6-4075-bef6-c0ef3a7026b4")
BOLNA_API_URL = "https://api.bolna.ai"

app = FastAPI(
    title="Bolna to Slack Integration",
    description="Trigger Bolna calls and receive Slack alerts when calls end",
    version="1.0.0"
)


# Pydantic Models
class TelephonyData(BaseModel):
    duration: Optional[str] = None
    to_number: Optional[str] = None
    from_number: Optional[str] = None
    recording_url: Optional[str] = None
    call_type: Optional[str] = None
    hangup_by: Optional[str] = None
    hangup_reason: Optional[str] = None


class BolnaWebhookPayload(BaseModel):
    model_config = {"extra": "allow"}
    id: str
    agent_id: str
    conversation_time: Optional[float] = None
    status: str
    transcript: Optional[str] = None
    telephony_data: Optional[TelephonyData] = None
    extracted_data: Optional[Dict[str, Any]] = None


class MakeCallRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number with country code (e.g., +919876543210)")


class SimulateCallRequest(BaseModel):
    duration: float = Field(default=45.0)
    transcript: str = Field(default="Agent: Hello! How can I help you today?\n\nUser: I wanted to know about your services.\n\nAgent: We offer voice AI solutions. Would you like more details?\n\nUser: Yes, that sounds great!\n\nAgent: I'll have our team reach out. Have a wonderful day!")


# Helper Functions
def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "N/A"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs}s" if minutes > 0 else f"{secs}s"


async def send_slack_alert(call_data: BolnaWebhookPayload) -> bool:
    if not SLACK_WEBHOOK_URL:
        print("Error: SLACK_WEBHOOK_URL not configured")
        return False

    duration = call_data.conversation_time
    if duration is None and call_data.telephony_data:
        try:
            duration = float(call_data.telephony_data.duration or 0)
        except ValueError:
            duration = None

    transcript = call_data.transcript or "No transcript available"
    if len(transcript) > 2500:
        transcript = transcript[:2500] + "... [truncated]"

    slack_payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Bolna Call Ended", "emoji": True}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Call ID:*\n`{call_data.id}`"},
                {"type": "mrkdwn", "text": f"*Agent ID:*\n`{call_data.agent_id}`"}
            ]},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Duration:*\n{format_duration(duration)}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{call_data.status}"}
            ]},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Transcript:*\n```{transcript}```"}}
        ],
        "text": f"Bolna Call Ended - ID: {call_data.id}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(SLACK_WEBHOOK_URL, json=slack_payload, timeout=10.0)
            response.raise_for_status()
            return True
    except httpx.HTTPError as e:
        print(f"Slack error: {e}")
        return False


# HTML Template
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bolna to Slack Integration</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
        .container { background: white; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; max-width: 500px; width: 100%; }
        h1 { color: #333; margin-bottom: 10px; font-size: 24px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        input[type="tel"] { width: 100%; padding: 12px 16px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 16px; }
        input[type="tel"]:focus { outline: none; border-color: #667eea; }
        .hint { font-size: 12px; color: #888; margin-top: 6px; }
        .btn { width: 100%; padding: 14px; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; margin-bottom: 10px; }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .btn-success { background: #28a745; }
        .result { margin-top: 15px; padding: 16px; border-radius: 8px; display: none; }
        .result.success { background: #d4edda; color: #155724; display: block; }
        .result.error { background: #f8d7da; color: #721c24; display: block; }
        .divider { height: 1px; background: #e1e1e1; margin: 25px 0; }
        .info-box { background: #f8f9fa; border-radius: 8px; padding: 16px; margin-top: 20px; }
        .info-box h3 { font-size: 14px; color: #333; margin-bottom: 10px; }
        .info-box p { font-size: 13px; color: #666; line-height: 1.6; }
        .links { margin-top: 20px; display: flex; gap: 12px; }
        .links a { padding: 8px 16px; background: #f0f0f0; color: #333; text-decoration: none; border-radius: 6px; font-size: 13px; }
        .links a:hover { background: #e0e0e0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Bolna to Slack Integration</h1>
        <p class="subtitle">Make Voice AI calls and receive Slack notifications</p>
        
        <form id="callForm">
            <div class="form-group">
                <label for="phone">Phone Number</label>
                <input type="tel" id="phone" placeholder="+919876543210" required>
                <p class="hint">Include country code (E.164 format)</p>
            </div>
            <button type="submit" id="callBtn" class="btn btn-primary">Make Call</button>
        </form>
        <div id="callResult" class="result"></div>
        
        <div class="divider"></div>
        
        <h2 style="font-size: 16px; margin-bottom: 15px;">Test Without Credits</h2>
        <button type="button" id="simBtn" class="btn btn-success">Simulate Call</button>
        <div id="simResult" class="result"></div>
        
        <div class="info-box">
            <h3>How it works:</h3>
            <p><strong>Make Call:</strong> Real Bolna AI call to your phone<br>
            <strong>Simulate:</strong> Test Slack notification without credits</p>
        </div>
        
        <div class="links">
            <a href="/docs">API Docs</a>
            <a href="/health">Health</a>
        </div>
    </div>
    
    <script>
        async function apiCall(url, btn, resultDiv, successMsg) {
            btn.disabled = true;
            const origText = btn.textContent;
            btn.textContent = 'Processing...';
            resultDiv.className = 'result';
            
            try {
                const body = url === '/make-call' ? { phone_number: document.getElementById('phone').value } : {};
                const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
                const data = await res.json();
                
                if (res.ok) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = successMsg(data);
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = '<strong>Error:</strong> ' + (data.detail || 'Request failed');
                }
            } catch (e) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = '<strong>Error:</strong> ' + e.message;
            }
            
            btn.disabled = false;
            btn.textContent = origText;
        }
        
        document.getElementById('callForm').addEventListener('submit', (e) => {
            e.preventDefault();
            apiCall('/make-call', document.getElementById('callBtn'), document.getElementById('callResult'),
                (d) => '<strong>Call initiated!</strong><br>ID: ' + d.execution_id + '<br>Answer your phone!');
        });
        
        document.getElementById('simBtn').addEventListener('click', () => {
            apiCall('/simulate-call', document.getElementById('simBtn'), document.getElementById('simResult'),
                (d) => '<strong>Success!</strong><br>Call ID: ' + d.call_id + '<br>Check Slack for notification!');
        });
    </script>
</body>
</html>
"""


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE


@app.post("/make-call")
async def make_call(request: MakeCallRequest):
    if not BOLNA_API_KEY:
        raise HTTPException(status_code=500, detail="BOLNA_API_KEY not configured")
    
    phone = request.phone_number.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOLNA_API_URL}/call",
                json={"agent_id": BOLNA_AGENT_ID, "recipient_phone_number": phone},
                headers={"Authorization": f"Bearer {BOLNA_API_KEY}", "Content-Type": "application/json"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"message": "Call initiated", "execution_id": data.get("execution_id"), "status": data.get("status")}
            else:
                raise HTTPException(status_code=response.status_code, detail="Bolna API error")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


@app.post("/simulate-call")
async def simulate_call(request: SimulateCallRequest = SimulateCallRequest()):
    simulated = BolnaWebhookPayload(
        id=str(uuid.uuid4()),
        agent_id=BOLNA_AGENT_ID,
        conversation_time=request.duration,
        status="completed",
        transcript=request.transcript,
        telephony_data=TelephonyData(duration=str(int(request.duration)), to_number="+919876543210", call_type="outbound")
    )
    
    if await send_slack_alert(simulated):
        return {"message": "Simulation successful", "call_id": simulated.id, "slack_notification": "sent"}
    raise HTTPException(status_code=500, detail="Failed to send Slack notification")


@app.post("/webhook/bolna")
async def bolna_webhook(payload: BolnaWebhookPayload):
    print(f"Webhook received: call={payload.id}, status={payload.status}")
    
    if payload.status == "completed":
        success = await send_slack_alert(payload)
        return {"message": "Slack alert sent" if success else "Failed to send alert", "call_id": payload.id}
    
    return {"message": f"Received status: {payload.status}", "call_id": payload.id}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "bolna_configured": bool(BOLNA_API_KEY),
        "slack_configured": bool(SLACK_WEBHOOK_URL)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    print(f"Server: http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
