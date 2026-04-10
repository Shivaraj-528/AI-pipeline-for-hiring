# agents/final_decision_agent.py
# ─────────────────────────────────────────────────────────────────────
# Stage 6 — Final Decision Agent
# Reads the evaluation result and routes actions:
#   PASS → Slack HR notification + Candidate selection email + DB record
#   FAIL → Slack HR rejection notification + DB record
# Author  : Shivaraj Yelugodla  |  Date: 07-Mar-2026
# ─────────────────────────────────────────────────────────────────────

import os
import requests
from dotenv import load_dotenv
from utils.email_service import send_selection_email
from utils.resume_parser import extract_email
from utils.json_store import store_candidate_json

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_notification(message):
    if not SLACK_WEBHOOK_URL:
        print("⚠️  Slack webhook not configured in .env")
        return False

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Slack notification sent successfully.")
            return True
        else:
            print(f"❌ Slack notification failed. Status: {response.status_code} | Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Slack Error: No internet connection or webhook URL unreachable.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Slack Error: Request timed out.")
        return False
    except Exception as e:
        print(f"❌ Slack Error: {str(e)}")
        return False


def handle_final_decision(evaluation_result, resume_text=None):
    decision = "Fail"

    for line in evaluation_result.splitlines():
        if line.startswith("Decision"):
            decision = line.split(":", 1)[1].strip()
            break

    # Extract candidate email from resume if provided
    candidate_email = None
    if resume_text:
        candidate_email = extract_email(resume_text)

    if decision.lower() == "pass":
        # --- PASS: Notify HR on Slack + send selection email + store record ---
        slack_message = (
            "🎉 *Candidate Shortlisted for Round 2!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 *Company:* AgentForge Technologies\n"
            f"{evaluation_result}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_slack_notification(slack_message)

        # Send selection email to candidate
        if candidate_email:
            send_selection_email(candidate_email)
            print(f"📧 Selection email sent to {candidate_email}")
        else:
            print("⚠️  Could not extract candidate email — skipping selection email.")

        # Store in JSON database
        store_candidate_json({
            "decision": "Pass",
            "evaluation_summary": evaluation_result,
            "remarks": "Selected by AI hiring system"
        })

    else:
        # --- FAIL: Notify HR on Slack about rejection ---
        slack_message = (
            "❌ *Candidate Did Not Clear the Interview*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏢 *Company:* AgentForge Technologies\n"
            f"{evaluation_result}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_slack_notification(slack_message)
        print("❌ Candidate rejected. HR notified on Slack.")

        # Store rejection in JSON database
        store_candidate_json({
            "decision": "Fail",
            "evaluation_summary": evaluation_result,
            "remarks": "Rejected by AI hiring system"
        })
