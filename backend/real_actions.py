"""
InsightFlow Real Action Executors
Replaces simulation with actual API calls for steps 2, 3, and 4.

Environment variables (set before running the server):
  SMTP_USER          Gmail address used to send alerts
  SMTP_PASS          Gmail App Password (16-char, no spaces)
  NOTIFY_EMAIL       Recipient address for stakeholder alerts
  GOOGLE_SHEET_ID    ID from your Google Sheet URL
  GOOGLE_SA_JSON     Full JSON of a GCP service-account key (single-line)
  SLACK_WEBHOOK_URL  Incoming-webhook URL from Slack (optional)

If any variable is missing the step falls back to a rich simulation
so the demo never crashes.
"""

import json
import logging
import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

logger = logging.getLogger("insightflow.real_actions")

# ── env vars ──────────────────────────────────────────────────────────────────
SMTP_USER       = os.environ.get("SMTP_USER", "")
SMTP_PASS       = os.environ.get("SMTP_PASS", "")
NOTIFY_EMAIL    = os.environ.get("NOTIFY_EMAIL", "")
SHEET_ID        = os.environ.get("GOOGLE_SHEET_ID", "")
SA_JSON         = os.environ.get("GOOGLE_SA_JSON", "")
SLACK_WEBHOOK   = os.environ.get("SLACK_WEBHOOK_URL", "")


# ── Step 2 — Real email notification ─────────────────────────────────────────
def step2_notify_stakeholders(action_text: str, domain: str, insight: str) -> dict:
    """Send a real HTML stakeholder alert email."""
    if not (SMTP_USER and SMTP_PASS and NOTIFY_EMAIL):
        logger.info("[REAL-ACTIONS] Email not configured — rich simulation")
        return _sim_email(action_text, domain)

    subject = f"[InsightFlow Alert] {domain} — Autonomous Action Triggered"
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#050508;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:#4f8ef7;margin:0">InsightFlow Autonomous Agent Alert</h2>
        <p style="color:#94a3b8;margin:6px 0 0 0;font-size:13px">
          {domain} Domain · {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
        </p>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:0 0 8px 8px;padding:20px">
        <h3 style="color:#1e293b;margin-top:0">🔍 Insight Detected</h3>
        <p style="background:#fef3c7;border-left:4px solid #f59e0b;padding:10px 14px;border-radius:4px">
          {insight}
        </p>
        <h3 style="color:#1e293b">⚡ Action Triggered</h3>
        <p style="color:#334155">{action_text}</p>
        <h3 style="color:#1e293b">📊 System Status</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          <tr style="background:#f1f5f9">
            <td style="padding:8px;border:1px solid #e2e8f0;font-weight:bold">Domain</td>
            <td style="padding:8px;border:1px solid #e2e8f0">{domain}</td>
          </tr>
          <tr>
            <td style="padding:8px;border:1px solid #e2e8f0;font-weight:bold">Triggered at</td>
            <td style="padding:8px;border:1px solid #e2e8f0">{datetime.utcnow().isoformat()}</td>
          </tr>
          <tr style="background:#f1f5f9">
            <td style="padding:8px;border:1px solid #e2e8f0;font-weight:bold">Engine</td>
            <td style="padding:8px;border:1px solid #e2e8f0">InsightFlow v2.0</td>
          </tr>
        </table>
        <p style="color:#64748b;font-size:11px;margin-top:16px">
          This alert was generated autonomously by the InsightFlow agentic pipeline.
          No human triggered this email.
        </p>
      </div>
    </body></html>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = NOTIFY_EMAIL
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.send_message(msg)

        logger.info(f"[REAL-ACTIONS] Email sent → {NOTIFY_EMAIL}")
        return {
            "real": True,
            "channel": "email",
            "to": NOTIFY_EMAIL,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "http_status": 250,
        }
    except Exception as exc:
        logger.warning(f"[REAL-ACTIONS] Email failed ({exc}) — falling back to simulation")
        result = _sim_email(action_text, domain)
        result["fallback_reason"] = str(exc)
        return result


def _sim_email(action_text: str, domain: str) -> dict:
    time.sleep(0.15)
    return {
        "real": False,
        "channel": "email_simulated",
        "to": NOTIFY_EMAIL or "stakeholders@company.com",
        "subject": f"[InsightFlow Alert] {domain} — Autonomous Action Triggered",
        "body_preview": action_text[:120],
        "sent_at": datetime.utcnow().isoformat(),
        "http_status": 200,
        "note": "Set SMTP_USER / SMTP_PASS / NOTIFY_EMAIL to send a real email",
    }


# ── Step 3 — Real Google Sheets update ───────────────────────────────────────
def step3_update_system_state(domain: str, state_data: dict) -> dict:
    """Append a row to the real InsightFlow Google Sheet dashboard."""
    if not (SHEET_ID and SA_JSON):
        logger.info("[REAL-ACTIONS] Google Sheets not configured — rich simulation")
        return _sim_sheet(domain, state_data)

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(
            json.loads(SA_JSON),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        client = gspread.authorize(creds)
        sheet  = client.open_by_key(SHEET_ID).sheet1

        # Ensure header row exists
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Timestamp":
            sheet.insert_row(
                ["Timestamp", "Domain", "Status", "Actions Done",
                 "Cost PKR", "Risk Level", "Source"],
                index=1,
            )

        row = [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            domain,
            state_data.get("status", "updated"),
            state_data.get("actions_completed", 0),
            state_data.get("total_cost_pkr", 0),
            state_data.get("risk_level", "REDUCED"),
            "InsightFlow",
        ]
        sheet.append_row(row)

        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        logger.info(f"[REAL-ACTIONS] Google Sheet updated — {sheet_url}")
        return {
            "real": True,
            "channel": "google_sheets",
            "sheet_id": SHEET_ID,
            "sheet_url": sheet_url,
            "row_appended": row,
            "updated_at": datetime.utcnow().isoformat(),
            "http_status": 200,
        }
    except ImportError:
        logger.warning("[REAL-ACTIONS] gspread not installed — pip install gspread google-auth")
        return _sim_sheet(domain, state_data)
    except Exception as exc:
        logger.warning(f"[REAL-ACTIONS] Sheet update failed ({exc}) — falling back")
        result = _sim_sheet(domain, state_data)
        result["fallback_reason"] = str(exc)
        return result


def _sim_sheet(domain: str, state_data: dict) -> dict:
    time.sleep(0.12)
    return {
        "real": False,
        "channel": "google_sheets_simulated",
        "sheet_id": SHEET_ID or "set-GOOGLE_SHEET_ID-env-var",
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}" if SHEET_ID else "not configured",
        "row_appended": [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            domain,
            state_data.get("status", "updated"),
            state_data.get("actions_completed", 0),
            state_data.get("total_cost_pkr", 0),
            "REDUCED",
            "InsightFlow",
        ],
        "updated_at": datetime.utcnow().isoformat(),
        "http_status": 200,
        "note": "Set GOOGLE_SHEET_ID + GOOGLE_SA_JSON to write to a real sheet",
    }


# ── Step 4 — Real webhook / Slack notification ────────────────────────────────
def step4_launch_mitigation(action_text: str, domain: str, cost_pkr: int) -> dict:
    """Fire a real Slack webhook with the mitigation alert."""
    if not SLACK_WEBHOOK:
        logger.info("[REAL-ACTIONS] Slack webhook not configured — rich simulation")
        return _sim_webhook(action_text, domain, cost_pkr)

    payload = {
        "text": f"*[InsightFlow Mitigation Launch]* {domain}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "InsightFlow — Mitigation Launched"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Domain:*\n{domain}"},
                    {"type": "mrkdwn", "text": f"*Cost:*\nPKR {cost_pkr:,}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.utcnow().strftime('%H:%M UTC')}"},
                    {"type": "mrkdwn", "text": f"*Source:*\nInsightFlow"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Action:*\n{action_text[:200]}"},
            },
        ],
    }
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(SLACK_WEBHOOK, json=payload)
        logger.info(f"[REAL-ACTIONS] Slack webhook fired — status {r.status_code}")
        return {
            "real": True,
            "channel": "slack_webhook",
            "webhook_url": SLACK_WEBHOOK[:40] + "...",
            "http_status": r.status_code,
            "fired_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.warning(f"[REAL-ACTIONS] Webhook failed ({exc}) — falling back")
        result = _sim_webhook(action_text, domain, cost_pkr)
        result["fallback_reason"] = str(exc)
        return result


def _sim_webhook(action_text: str, domain: str, cost_pkr: int) -> dict:
    time.sleep(0.10)
    return {
        "real": False,
        "channel": "slack_webhook_simulated",
        "payload_preview": {
            "domain": domain,
            "action": action_text[:100],
            "cost_pkr": cost_pkr,
        },
        "http_status": 200,
        "fired_at": datetime.utcnow().isoformat(),
        "note": "Set SLACK_WEBHOOK_URL env var to fire a real Slack message",
    }
