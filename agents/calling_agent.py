import os
import requests
import time
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


def extract_transcript_from_response(call_data):
    """
    Extract transcript from VAPI call response.
    Handles both simple transcript string and messages array format.
    """
    # Check if simple transcript exists
    if 'transcript' in call_data and call_data['transcript']:
        return call_data['transcript']
    
    # Otherwise, build from messages array
    if 'messages' in call_data and call_data['messages']:
        transcript_lines = []
        for msg in call_data['messages']:
            role = msg.get('role', 'unknown')
            message = msg.get('message', '') or msg.get('content', '')
            
            # Map role to readable name
            if role == 'assistant' or role == 'bot':
                speaker = "Interviewer"
            elif role == 'user':
                speaker = "Candidate"
            else:
                speaker = role.capitalize()
            
            if message:
                transcript_lines.append(f"{speaker}: {message}")
        
        return "\n\n".join(transcript_lines)
    
    return None


def wait_for_call_completion(call_id, max_wait_minutes=15):
    """
    Poll VAPI API to check if call is completed.
    Returns the transcript when call is done, or None if timeout/error.
    
    Args:
        call_id: The VAPI call ID
        max_wait_minutes: Maximum time to wait (default 15 minutes)
    
    Returns:
        str: The interview transcript, or None if failed/timeout
    """
    if not VAPI_API_KEY:
        print("❌ VAPI API key not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}"
    }
    
    poll_interval = 10  # seconds
    max_attempts = (max_wait_minutes * 60) // poll_interval
    attempt = 0
    
    print(f"\n⏳ Polling VAPI API for call completion (max wait: {max_wait_minutes} minutes)...")
    print(f"📞 Call ID: {call_id}")
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            # Get call status from VAPI API
            response = requests.get(
                f"https://api.vapi.ai/call/{call_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"⚠️ API error (attempt {attempt}/{max_attempts}): {response.status_code}")
                time.sleep(poll_interval)
                continue
            
            call_data = response.json()
            status = call_data.get('status', 'unknown')
            
            # Print status update every 6 attempts (1 minute)
            if attempt % 6 == 0:
                elapsed_minutes = (attempt * poll_interval) // 60
                print(f"   Status: {status} | Elapsed: {elapsed_minutes} min")
            
            # Check if call is completed
            if status in ['ended', 'completed', 'finished']:
                print(f"\n✅ Call completed! Status: {status}")
                
                # Extract transcript
                transcript = extract_transcript_from_response(call_data)
                
                if transcript:
                    print(f"📝 Transcript received ({len(transcript)} characters)")
                    return transcript
                else:
                    print("⚠️ Warning: Call completed but no transcript found")
                    print("Call data keys:", list(call_data.keys()))
                    return None
            
            # Check if call failed
            elif status in ['failed', 'error', 'no-answer', 'busy']:
                print(f"\n❌ Call failed with status: {status}")
                ended_reason = call_data.get('endedReason', 'unknown')
                print(f"   Reason: {ended_reason}")
                return None
            
            # Call still in progress
            else:
                # Continue polling
                time.sleep(poll_interval)
        
        except Exception as e:
            print(f"⚠️ Error polling API (attempt {attempt}/{max_attempts}): {str(e)}")
            time.sleep(poll_interval)
    
    # Timeout
    print(f"\n❌ Timeout: Call did not complete within {max_wait_minutes} minutes")
    return None
