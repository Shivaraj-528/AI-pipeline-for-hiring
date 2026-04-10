# server.py
# ─────────────────────────────────────────────────────────────────────
# AgentForge — FastAPI REST Server
# Exposes the hiring pipeline as an API with real-time SSE log streaming.
# Author  : Shivaraj Yelugodla
# Date    : 07-Mar-2026
# Version : 2.0
# ─────────────────────────────────────────────────────────────────────
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
from agents.calling_agent import start_interview_call, wait_for_call_completion, extract_salary_from_transcript
from agents.anti_cheat_agent import run_anti_cheat_analysis
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision
from utils.resume_parser import extract_resume_text, extract_resume_data
from utils.db import (
    init_tables, upsert_candidate,
    save_screening_result, save_background_check,
    save_interview_session, save_evaluation_result,
    get_all_candidates, get_pipeline_stats, test_connection
)

app = FastAPI(title="AgentForge API")

# ── Init Supabase tables on startup ─────────────
@app.on_event("startup")
async def startup_event():
    init_tables()

# ── CORS for Next.js frontend ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory list that accumulates pipeline events for SSE streaming to the frontend
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


# ── Health & DB status ────────────────────────────
@app.get("/health")
async def health():
    db_ok = test_connection()
    return {"status": "ok", "supabase": "connected" if db_ok else "error"}


# ── Stream logs via SSE ───────────────────────────
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


# ── Start pipeline ─────────────────────────────────
@app.post("/start-process")
async def start_process(background_tasks: BackgroundTasks,
                        file: UploadFile = File(...),
                        phone: str = Form(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(run_hiring_pipeline, temp_path, phone)
    return {"status": "started", "file": file.filename}


# Core pipeline coroutine — runs all 6 stages sequentially in the background
async def run_hiring_pipeline(resume_path: str, phone: str):
    candidate_id = None
    try:
        execution_logs.clear()

        # 1. Extraction
        await log_event("Extractor", "Parsing Resume PDF...", {"status": "reading_bytes"})
        resume_text = extract_resume_text(resume_path)
        resume_data = extract_resume_data(resume_text)
        candidate_email = resume_data.get("email", "Unknown")
        candidate_phone_from_resume = resume_data.get("phone")
        await log_event("Extractor", "Data Extraction Complete",
                        {"email": candidate_email, "phone": candidate_phone_from_resume}, "success")

        # ── Save candidate to Supabase ──
        candidate_id = upsert_candidate(
            email=candidate_email,
            phone=phone,
            resume_text=resume_text,
        )
        await log_event("Database", f"Candidate saved (id={candidate_id})",
                        {"candidate_id": candidate_id}, "success")

        # 2. Screening
        await log_event("Screening Agent", "Analyzing candidate fit score...",
                        {"logic": "Matching keywords & experience"})
        screening_result = screen_resume(resume_text)
        if candidate_id:
            save_screening_result(candidate_id, screening_result)
        await log_event("Screening Agent", "Screening Complete",
                        {"result": screening_result}, "success")

        if "qualified" not in screening_result.lower():
            await log_event("System", "Candidate rejected during screening", status="failed")
            return

        # 3. Verification
        await log_event("Verification Agent", "Verifying background credentials...",
                        {"targets": ["LinkedIn", "GitHub", "Email"]})
        verification_result = verify_background(resume_text, candidate_email)
        if candidate_id:
            save_background_check(candidate_id, verification_result)
        await log_event("Verification Agent", "Verification Complete",
                        verification_result, "success")

        if verification_result["credibility_score"] < 70:
            await log_event("System", "Candidate failed background check", status="failed")
            return

        # 4. Interview Prep
        await log_event("Logic Agent", "Generating tailored interview questions...",
                        {"mode": "Dynamic"})
        questions = generate_interview_questions(resume_text)
        await log_event("Logic Agent", "Questions Generated",
                        {"count": len(questions.split('\n'))}, "success")

        # 5. Live Call
        await log_event("Voice Agent", f"Initiating live call to {phone}...",
                        {"service": "Vapi.ai"})
        salary_budget = "8-15 LPA"
        call_response = start_interview_call(phone, questions, salary_budget=salary_budget)
        call_id = call_response.get('id') if call_response else None
        await log_event("Voice Agent", "Call Active",
                        {"call_id": call_id, "status": "ongoing"}, "status")

        transcript = wait_for_call_completion(call_id) if call_id else None

        if transcript:
            # Save completed interview session
            if candidate_id:
                save_interview_session(
                    candidate_id=candidate_id,
                    call_id=call_id or "unknown",
                    phone_number=phone,
                    questions=questions,
                    transcript=transcript,
                    call_status="completed"
                )
            await log_event("Voice Agent", "Call Completed",
                            {"transcript_length": len(transcript)}, "success")

            # 5b. Salary Negotiation Summary
            salary_info = extract_salary_from_transcript(transcript)
            await log_event("Salary Agent", "Salary Negotiation Analyzed", {
                "current_ctc": salary_info.get("current_ctc", "Not disclosed"),
                "expected_ctc": salary_info.get("expected_ctc", "Not disclosed"),
                "negotiation_status": salary_info.get("negotiation_status"),
                "within_budget": salary_info.get("within_budget")
            }, "success")

            # 5c. Anti-Cheat Analysis
            await log_event("Anti-Cheat Agent", "Running cheat detection analysis...",
                            {"checks": ["Latency", "Fluency", "Curveballs"]})
            cheat_report = run_anti_cheat_analysis(transcript, resume_text)
            curveball_list = cheat_report.get("curveball_questions", {}).get("questions", [])
            await log_event("Anti-Cheat Agent", "Analysis Complete", {
                "overall_risk": cheat_report.get("overall_risk"),
                "cheat_score": cheat_report.get("overall_score"),
                "latency_risk": cheat_report.get("latency_analysis", {}).get("risk"),
                "fluency_risk": cheat_report.get("fluency_analysis", {}).get("risk"),
                "curveball_questions": curveball_list,
                "recommendation": cheat_report.get("recommendation")
            }, "success")

            # 6. Evaluation
            await log_event("Evaluation Agent", "Analyzing interview transcript...",
                            {"metrics": ["Sentiment", "Technical Accuracy"]})
            evaluation = evaluate_interview(resume_text, transcript)
            if candidate_id:
                save_evaluation_result(candidate_id, evaluation)
            await log_event("Evaluation Agent", "Evaluation Complete",
                            {"summary": evaluation[:100] + "..."}, "success")

            # 7. Final Decision
            await log_event("Final Decision Agent", "Synthesizing final verdict...",
                            {"status": "finalizing"})
            handle_final_decision(evaluation, resume_text=resume_text)
            await log_event("System", "PROCESS COMPLETE",
                            {"decision": "Decision Processed & HR Notified"}, "success")
        else:
            # Save no-answer session
            if candidate_id:
                save_interview_session(
                    candidate_id=candidate_id,
                    call_id=call_id or "unknown",
                    phone_number=phone,
                    questions=questions,
                    transcript=None,
                    call_status="no-answer"
                )
            await log_event("Voice Agent", "Call failed or transcript unavailable",
                            status="failed")

    except Exception as e:
        await log_event("System", f"Critical Error: {str(e)}", status="failed")
    finally:
        if os.path.exists(resume_path):
            os.remove(resume_path)


# ── Dashboard data endpoints ─────────────────────
@app.get("/candidates")
async def list_candidates():
    """Return all candidates with their final decision."""
    return get_all_candidates()


@app.get("/stats")
async def pipeline_stats():
    """Return aggregate pipeline statistics."""
    return get_pipeline_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
