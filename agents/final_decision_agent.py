# agents/final_decision_agent.py

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
        print("Slack webhook not configured.")
        return

    payload = {
        "text": message
    }

    requests.post(SLACK_WEBHOOK_URL, json=payload)


def handle_final_decision(evaluation_result):
    decision = "Fail"

    for line in evaluation_result.splitlines():
        if line.startswith("Decision"):
            decision = line.split(":")[1].strip()
            break

    if decision.lower() == "pass":
        message = (
            "✅ *Candidate Shortlisted for Round 2*\n"
            "Company: Arya Stack Technologies\n"
            f"{evaluation_result}"
        )
        send_slack_notification(message)
        print("HR notified on Slack.")

        store_candidate_json({
            "decision": "Pass",
            "evaluation_summary": evaluation_result,
            "remarks": "Selected by AI hiring system"
        })

    else:
        print("Candidate rejected. Sending rejection email/message.")


