import os
import requests
import time
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")


def start_interview_call(phone_number, questions, salary_budget="8-15 LPA"):
    if not VAPI_API_KEY or not VAPI_ASSISTANT_ID or not VAPI_PHONE_NUMBER_ID:
        print("VAPI configuration missing.")
        return None

    # Sanitize phone number: remove all non-digit characters except the leading '+'
    sanitized_number = "".join([c for c in phone_number if c.isdigit() or (c == '+' and phone_number.index(c) == 0)])
    
    # Ensure it starts with '+'
    if not sanitized_number.startswith('+'):
        sanitized_number = '+' + sanitized_number

    print(f"📞 Attempting to call: {sanitized_number}")

    system_prompt = f"""You are a professional technical interviewer at AgentForge Technologies conducting a phone interview for a MERN Stack Developer position.

Your job has TWO PHASES:
  PHASE 1 — Ask the candidate the technical interview questions ONE AT A TIME.
  PHASE 2 — After ALL technical questions, conduct a brief salary negotiation.

INTERVIEW QUESTIONS:
{questions}

───── PHASE 1: TECHNICAL INTERVIEW ─────
- Start by greeting the candidate and asking if they are ready to begin.
- Ask each question clearly, one at a time, in order.
- After the candidate answers, briefly acknowledge their response and move to the next question.
- If the candidate gives a very short or vague answer, ask them to elaborate before moving on.
- If the candidate says they don't know, note it and move to the next question.
- Do NOT skip any questions.
- Do NOT give hints, answers, or explanations to the questions.

───── PHASE 2: SALARY NEGOTIATION (after all technical questions) ─────
Once ALL technical questions have been answered, transition naturally:
1. Say: "Great, thank you for your answers. Before we wrap up, I'd like to briefly discuss compensation expectations."
2. Ask: "What is your current CTC or last drawn salary?"
3. Ask: "What is your expected salary for this role?"
4. Our company budget for this role is {salary_budget}. Based on their answer:
   - If their expectation is WITHIN the budget: Say "That sounds within our range. Our team will discuss the specifics with you."
   - If their expectation is SLIGHTLY ABOVE the budget (up to 20% over): Say "We appreciate your expectations. Our budget for this role is around {salary_budget}. Would you be open to discussing a figure within that range?" If they agree, acknowledge positively. If they decline, note it politely.
   - If their expectation is FAR ABOVE the budget: Say "Thank you for sharing that. Our current budget for this position is {salary_budget}. I'll make sure the HR team is aware of your expectations for further discussion."
5. Do NOT promise any specific number. Just gather information and set expectations.
6. After salary discussion, thank the candidate and tell them the team will be in touch soon.

───── GENERAL RULES ─────
- Stay professional, calm, and encouraging throughout.
- Keep the conversation strictly on topic.
- Never reveal the exact maximum budget — only the range."""

    call_payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": sanitized_number
        },
        "assistantOverrides": {
            "firstMessage": (
                "Hello! Thank you for joining this interview call from AgentForge Technologies. "
                "I'm your AI technical interviewer for the MERN Stack Developer position. "
                "Are you ready to begin?"
            ),
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            }
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
                ended_reason = call_data.get('endedReason', 'unknown')
                print(f"\n✅ Call ended! Status: {status} | Reason: {ended_reason}")
                
                # If the call ended without being answered, treat as failure
                if ended_reason in ['customer-did-not-answer', 'no-answer', 'customer-busy', 'voicemail']:
                    print(f"❌ Candidate did not answer. Reason: {ended_reason}")
                    return None
                
                # Extract transcript
                transcript = extract_transcript_from_response(call_data)
                
                if transcript:
                    print(f"📝 Transcript received ({len(transcript)} characters)")
                    return transcript
                else:
                    print("⚠️ Call ended but no transcript found.")
                    print(f"   endedReason: {ended_reason}")
                    print("   Call data keys:", list(call_data.keys()))
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


def extract_salary_from_transcript(transcript):
    """
    Extract salary-related information from the interview transcript.
    Returns a dict with current_ctc, expected_ctc, and negotiation_status.
    """
    import re

    result = {
        "current_ctc": None,
        "expected_ctc": None,
        "negotiation_status": "not_discussed",
        "within_budget": None,
        "raw_salary_discussion": ""
    }

    if not transcript:
        return result

    lines = transcript.strip().splitlines()
    salary_section = []
    in_salary_section = False

    # Detect where salary discussion starts
    salary_keywords = ["salary", "ctc", "compensation", "package", "lpa", "lakhs",
                       "expected", "current", "drawn", "offer", "budget", "pay"]

    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in salary_keywords):
            in_salary_section = True
        if in_salary_section:
            salary_section.append(line)

    result["raw_salary_discussion"] = "\n".join(salary_section)

    # Try to extract numbers (e.g., "12 LPA", "8 lakhs", "₹15,00,000")
    salary_pattern = r'(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lakh|lac)'
    numbers_found = re.findall(salary_pattern, transcript.lower())

    if len(numbers_found) >= 2:
        result["current_ctc"] = f"{numbers_found[0]} LPA"
        result["expected_ctc"] = f"{numbers_found[1]} LPA"
    elif len(numbers_found) == 1:
        result["expected_ctc"] = f"{numbers_found[0]} LPA"

    # Detect negotiation outcome
    transcript_lower = transcript.lower()
    if "within our range" in transcript_lower or "sounds good" in transcript_lower:
        result["negotiation_status"] = "within_budget"
        result["within_budget"] = True
    elif "open to discussing" in transcript_lower or "would you be open" in transcript_lower:
        result["negotiation_status"] = "negotiable"
        result["within_budget"] = None  # needs HR follow-up
    elif "budget for this position" in transcript_lower or "far above" in transcript_lower:
        result["negotiation_status"] = "above_budget"
        result["within_budget"] = False

    if salary_section:
        result["negotiation_status"] = result["negotiation_status"] if result["negotiation_status"] != "not_discussed" else "discussed"

    return result
