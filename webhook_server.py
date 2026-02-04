# webhook_server.py

from fastapi import FastAPI, Request
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision

app = FastAPI()

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    payload = await request.json()

    event_type = payload.get("type")
    data = payload.get("data", {})

    print("\n📩 Webhook received:", event_type)

    # Only act when the call is completed
    if event_type == "call.completed":
        transcript = data.get("transcript")

        if not transcript:
            print("⚠️ No transcript found.")
            return {"status": "no transcript"}

        print("\n📞 Call completed. Transcript received.\n")

        evaluation = evaluate_interview(
            resume_text="(resume already known)",
            interview_transcript=transcript
        )

        print("\n--- INTERVIEW EVALUATION ---")
        print(evaluation)
        print("---------------------------\n")

        handle_final_decision(evaluation)

        return {"status": "evaluation completed"}

    return {"status": "event ignored"}
