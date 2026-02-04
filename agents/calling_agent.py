import os
import requests
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")


def start_interview_call(phone_number, questions):
    if not VAPI_API_KEY or not VAPI_ASSISTANT_ID or not VAPI_PHONE_NUMBER_ID:
        print("VAPI configuration missing.")
        return None

    call_payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": phone_number
        }
    }

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.vapi.ai/call",
        json=call_payload,
        headers=headers
    )

    if response.status_code in [200, 201, 202]:
        print("Interview call started successfully.")
        return response.json()
    else:
        print("Failed to start call:", response.text)
        return None
