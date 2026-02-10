from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio
import os
import shutil
from agents.resume_screening_agent import screen_resume
from agents.background_verification_agent import verify_background
from agents.interview_question_agent import generate_interview_questions
from agents.calling_agent import start_interview_call, wait_for_call_completion
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision
from utils.resume_parser import extract_resume_text, extract_resume_data

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state to store logs for streaming
execution_logs = []

async def log_event(agent: str, message: str, data: dict = None, status: str = "processing"):
    event = {
        "agent": agent,
        "message": message,
        "data": data,
        "status": status,
        "timestamp": asyncio.get_event_loop().time()
    }
    execution_logs.append(event)
    return event

@app.get("/stream-logs")
async def stream_logs():
    async def event_generator():
        last_index = 0
        while True:
            if last_index < len(execution_logs):
                for i in range(last_index, len(execution_logs)):
                    yield f"data: {json.dumps(execution_logs[i])}\n\n"
                last_index = len(execution_logs)
            await asyncio.sleep(0.5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/start-process")
async def start_process(background_tasks: BackgroundTasks, file: UploadFile = File(...), phone: str = Form(...)):
    # Save temporary file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    background_tasks.add_task(run_hiring_pipeline, temp_path, phone)
    return {"status": "started", "file": file.filename}

async def run_hiring_pipeline(resume_path: str, phone: str):
    try:
        execution_logs.clear()
        
        # 1. Extraction
        await log_event("Extractor", "Parsing Resume PDF...", {"status": "reading_bytes"})
        resume_text = extract_resume_text(resume_path)
        resume_data = extract_resume_data(resume_text)
        candidate_email = resume_data.get("email", "Unknown")
        await log_event("Extractor", "Data Extraction Complete", {"email": candidate_email}, "success")

        # 2. Screening
        await log_event("Screening Agent", "Analyzing candidate fit score...", {"logic": "Matching keywords & experience"})
        screening_result = screen_resume(resume_text)
        await log_event("Screening Agent", "Screening Complete", {"result": screening_result}, "success")

        if "qualified" not in screening_result.lower():
            await log_event("System", "Candidate rejected during screening", status="failed")
            return

        # 3. Verification
        await log_event("Verification Agent", "Verifying background credentials...", {"targets": ["LinkedIn", "GitHub", "Email"]})
        verification_result = verify_background(resume_text, candidate_email)
        await log_event("Verification Agent", "Verification Complete", verification_result, "success")

        if verification_result["credibility_score"] < 70:
            await log_event("System", "Candidate failed background check", status="failed")
            return

        # 4. Interview Prep
        await log_event("Logic Agent", "Generating tailored interview questions...", {"mode": "Dynamic"})
        questions = generate_interview_questions(resume_text)
        await log_event("Logic Agent", "Questions Generated", {"count": len(questions.split('\n'))}, "success")

        # 5. Live Call
        await log_event("Voice Agent", f"Initiating live call to {phone}...", {"service": "RetellAI/ElevenLabs"})
        call_response = start_interview_call(phone, questions)
        call_id = call_response.get('id')
        await log_event("Voice Agent", "Call Active", {"call_id": call_id, "status": "ongoing"}, "status")

        # Wait for completion (in a real app, this would be handled via webhook, 
        # but for this flow we wait as per main.py logic)
        transcript = wait_for_call_completion(call_id)
        
        if transcript:
            await log_event("Voice Agent", "Call Completed", {"transcript_length": len(transcript)}, "success")
            
            # 6. Evaluation
            await log_event("Evaluation Agent", "Analyzing interview transcript...", {"metrics": ["Sentiment", "Technical Accuracy"]})
            evaluation = evaluate_interview(resume_text, transcript)
            await log_event("Evaluation Agent", "Evaluation Complete", {"summary": evaluation[:100] + "..."}, "success")
            
            # 7. Final Decision
            await log_event("Final Decision Agent", "Synthesizing final verdict...", {"status": "finalizing"})
            handle_final_decision(evaluation)
            await log_event("System", "PROCESS COMPLETE", {"decision": "Decision Processed & HR Notified"}, "success")
        else:
            await log_event("Voice Agent", "Call failed or transcript unavailable", status="failed")

    except Exception as e:
        await log_event("System", f"Critical Error: {str(e)}", status="failed")
    finally:
        if os.path.exists(resume_path):
            os.remove(resume_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
