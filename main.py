# main.py
# ─────────────────────────────────────────────────────────────────────
# AgentForge — AI-Powered Technical Recruiter
# Entry Point: Runs the full end-to-end hiring pipeline from the CLI.
# Author  : Shivaraj Yelugodla
# Date    : 07-Mar-2026
# Version : 2.0
# ─────────────────────────────────────────────────────────────────────
import os
import time

from agents.calling_agent import start_interview_call, wait_for_call_completion, extract_salary_from_transcript
from agents.anti_cheat_agent import run_anti_cheat_analysis
from utils.resume_parser import extract_resume_text, extract_resume_data
from agents.resume_screening_agent import screen_resume
from agents.background_verification_agent import verify_background
from agents.interview_question_agent import generate_interview_questions
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision
from utils.db import (
    init_tables, upsert_candidate,
    save_screening_result, save_background_check,
    save_interview_session, save_evaluation_result
)

# ── Bootstrap DB tables on startup ──────────────
init_tables()

# Path to the candidate's resume file (PDF format expected)
resume_path = "resumes/resume.pdf"
# Path where the interview transcript will be saved after the call completes
transcript_path = "demo_assets/interview_transcript.txt"

# ✏️  UPDATE THIS to the candidate's real phone number before each run
PHONE_NUMBER = "+916300655054"

# 💰 Salary budget range for this role (used in AI salary negotiation on call)
SALARY_BUDGET = "8-15 LPA"


# ── Stage 1: Parse the resume to extract raw text and candidate details ──
print("\nParsing resume...\n")
resume_text = extract_resume_text(resume_path)
resume_data = extract_resume_data(resume_text)
candidate_email = resume_data["email"]
candidate_phone_in_resume = resume_data.get("phone")

print("Candidate Email:", candidate_email)
print(f"ℹ️  Phone found in resume: {candidate_phone_in_resume} (for reference only)")
print(f"📞 Calling number set in main.py: {PHONE_NUMBER}")

# ── Save candidate to Supabase ───────────────────
candidate_id = upsert_candidate(
    email=candidate_email,
    phone=PHONE_NUMBER,
    resume_text=resume_text,
)

print("Running resume screening agent...\n")
screening_result = screen_resume(resume_text)
print("--- SCREENING RESULT ---")
print(screening_result)
print("-----------------------\n")

# Save screening result
if candidate_id:
    save_screening_result(candidate_id, screening_result)

# Gate 1: Only proceed if the AI screening agent returns 'qualified'
if "qualified" not in screening_result.lower():
    print("❌ Candidate not qualified. Exiting.\n")
    exit(0)

# Background Verification
print("\n" + "="*60)
print("🔍 BACKGROUND VERIFICATION")
print("="*60 + "\n")

verification_result = verify_background(resume_text, candidate_email)

print("\n--- VERIFICATION RESULT ---")
print(f"Credibility Score: {verification_result['credibility_score']}/100")
print(f"Status: {verification_result['status']}")
print(f"Recommendation: {verification_result['recommendation']}")
if verification_result['issues']:
    print(f"Issues: {', '.join(verification_result['issues'])}")
print("---------------------------\n")

# Save background check
if candidate_id:
    save_background_check(candidate_id, verification_result)

# Check if verification passed
if verification_result["credibility_score"] < 70:
    print("❌ Background verification failed. Candidate rejected.\n")
    print(f"Reason: Credibility score ({verification_result['credibility_score']}) below threshold (70)")
    exit(0)

print("✅ Background verification passed. Proceeding to interview.\n")

# ── Stage 3: Generate personalised interview questions from the resume ──
print("Generating interview questions...\n")
questions = generate_interview_questions(resume_text)
print("--- INTERVIEW QUESTIONS ---")
print(questions)
print("---------------------------\n")

# ── Stage 4: Initiate the live AI phone interview via Vapi.ai ──
print("Starting live interview call...\n")

call_response = start_interview_call(
    phone_number=PHONE_NUMBER,
    questions=questions,
    salary_budget=SALARY_BUDGET
)

# Check if call was initiated successfully
if not call_response or 'id' not in call_response:
    print("❌ Failed to initiate call. Exiting.")
    exit(1)

call_id = call_response['id']
print(f"\n📞 Call initiated successfully!")
print(f"Call ID: {call_id}")
print(f"Status: {call_response.get('status', 'unknown')}")

# Wait for call to complete and get real transcript
print("\n" + "="*60)
print("⏳ WAITING FOR INTERVIEW TO COMPLETE...")
print("This may take 5-15 minutes depending on interview length.")
print("="*60)

interview_transcript = wait_for_call_completion(call_id, max_wait_minutes=15)

# Check if we got a transcript
if not interview_transcript:
    print("\n❌ Failed to retrieve transcript.")
    print("📧 Sending call booking email to candidate...")

    # Save no-answer session
    if candidate_id:
        save_interview_session(
            candidate_id=candidate_id,
            call_id=call_id,
            phone_number=PHONE_NUMBER,
            questions=questions,
            transcript=None,
            call_status="no-answer"
        )

    from utils.email_service import send_call_booking_email

    candidate_name = "Candidate"
    try:
        lines = resume_text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                candidate_name = line
                break
    except:
        pass

    email_sent = send_call_booking_email(candidate_email, candidate_name)

    if email_sent:
        print(f"✅ Call booking email sent to {candidate_email}")
        print(f"📅 Candidate can now schedule interview at their convenience")
        print("\n" + "="*60)
        print("⏸️  PROCESS PAUSED - WAITING FOR CANDIDATE TO BOOK SLOT")
        print("="*60)
    else:
        print("⚠️  Failed to send booking email. Please contact candidate manually.")

    exit(0)

# Save transcript to file for record-keeping
transcript_path = "demo_assets/interview_transcript.txt"
with open(transcript_path, "w") as file:
    file.write(interview_transcript)
print(f"\n💾 Transcript saved to: {transcript_path}")

# Save interview session to Supabase
if candidate_id:
    save_interview_session(
        candidate_id=candidate_id,
        call_id=call_id,
        phone_number=PHONE_NUMBER,
        questions=questions,
        transcript=interview_transcript,
        call_status="completed"
    )

# ── Stage 4B: Extract salary negotiation data from transcript ──
print("\n" + "="*60)
print("💰 SALARY NEGOTIATION SUMMARY")
print("="*60)
salary_info = extract_salary_from_transcript(interview_transcript)
print(f"   Current CTC:        {salary_info['current_ctc'] or 'Not disclosed'}")
print(f"   Expected CTC:       {salary_info['expected_ctc'] or 'Not disclosed'}")
print(f"   Negotiation Status: {salary_info['negotiation_status']}")
if salary_info['within_budget'] is True:
    print("   ✅ Within company budget")
elif salary_info['within_budget'] is False:
    print("   ⚠️  Above company budget — needs HR review")
else:
    print("   🔄 Negotiable / Pending HR discussion")
print("="*60 + "\n")

# ── Stage 4C: Anti-Cheat Analysis ──
print("\n" + "="*60)
print("🛡️  ANTI-CHEAT ANALYSIS")
print("="*60)

cheat_report = run_anti_cheat_analysis(interview_transcript, resume_text)

print(f"\n   Overall Risk:  {cheat_report['risk_emoji']} {cheat_report['overall_risk']}")
print(f"   Cheat Score:   {cheat_report['overall_score']}/100 (higher = more genuine)")
print(f"   Recommendation: {cheat_report['recommendation']}")

print("\n   ── Response Latency Analysis ──")
for d in cheat_report['latency_analysis']['details']:
    print(f"      {d}")

print("\n   ── Fluency Detection ──")
for d in cheat_report['fluency_analysis']['details']:
    print(f"      {d}")

if cheat_report['curveball_questions'].get('questions'):
    print("\n   ── Curveball Follow-up Questions ──")
    for i, q in enumerate(cheat_report['curveball_questions']['questions'], 1):
        print(f"      {i}. {q}")
        if i <= len(cheat_report['curveball_questions'].get('rationales', [])):
            print(f"         ↳ {cheat_report['curveball_questions']['rationales'][i-1]}")

print("\n" + "="*60 + "\n")

# ── Stage 5: Evaluate transcript — Python counting + LLM quality scoring ──
print("\n" + "="*60)
print("🤖 EVALUATING INTERVIEW...")
print("="*60 + "\n")

evaluation = evaluate_interview(resume_text, interview_transcript)

print("\n--- INTERVIEW EVALUATION ---")
print(evaluation)
print("-----------------------------\n")

# Save evaluation result to Supabase
if candidate_id:
    save_evaluation_result(candidate_id, evaluation)

# Parse decision for summary
decision_line = [l for l in evaluation.splitlines() if l.startswith("Decision")]
decision = decision_line[0].split(":")[1].strip() if decision_line else "Fail"

if decision.lower() == "pass":
    print("🎉 RESULT: CANDIDATE PASSED — Minimum 2 perfect answers achieved.")
else:
    print("❌ RESULT: CANDIDATE FAILED — Did not meet the minimum of 2 perfect answers.")

# ── Stage 6: Notify HR on Slack + email candidate + persist result to DB ──
print("\nHandling final decision...\n")
handle_final_decision(evaluation, resume_text=resume_text)
print("\n" + "="*60)
print("✅ HIRING PROCESS COMPLETED")
print("="*60 + "\n")
