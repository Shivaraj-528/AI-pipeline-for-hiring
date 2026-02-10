# main.py
import os
import time


from agents.calling_agent import start_interview_call, wait_for_call_completion
from utils.resume_parser import extract_resume_text
from agents.resume_screening_agent import screen_resume
from agents.background_verification_agent import verify_background
from agents.interview_question_agent import generate_interview_questions
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision

resume_path = "resumes/resume.pdf"
transcript_path = "demo_assets/interview_transcript.txt"

PHONE_NUMBER = "+916300655054"


print("\nParsing resume...\n")
resume_text = extract_resume_text(resume_path)

from utils.resume_parser import extract_resume_data

resume_data = extract_resume_data(resume_text)
candidate_email = resume_data["email"]

print("Candidate Email:", candidate_email)


print("Running resume screening agent...\n")
screening_result = screen_resume(resume_text)
print("--- SCREENING RESULT ---")
print(screening_result)
print("-----------------------\n")

# Check if candidate is qualified
if "qualified" not in screening_result.lower():
    print("❌ Candidate not qualified. Exiting.\n")
    exit(0)

# Background Verification (NEW)
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

# Check if verification passed
if verification_result["credibility_score"] < 70:
    print("❌ Background verification failed. Candidate rejected.\n")
    print(f"Reason: Credibility score ({verification_result['credibility_score']}) below threshold (70)")
    exit(0)

print("✅ Background verification passed. Proceeding to interview.\n")

print("Generating interview questions...\n")
questions = generate_interview_questions(resume_text)
print("--- INTERVIEW QUESTIONS ---")
print(questions)
print("---------------------------\n")

print("Starting live interview call...\n")

call_response = start_interview_call(
    phone_number=PHONE_NUMBER,
    questions=questions
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
    
    # Import email service
    from utils.email_service import send_call_booking_email
    
    # Extract candidate name from resume (simple extraction)
    candidate_name = "Candidate"
    try:
        # Try to extract name from resume text (usually first line or near email)
        lines = resume_text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            # Look for a line that might be a name (2-4 words, capitalized)
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                candidate_name = line
                break
    except:
        pass
    
    # Send booking email
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


# Evaluate the real interview transcript
print("\n" + "="*60)
print("🤖 EVALUATING INTERVIEW...")
print("="*60 + "\n")

evaluation = evaluate_interview(resume_text, interview_transcript)
print("\n--- INTERVIEW EVALUATION ---")
print(evaluation)
print("-----------------------------\n")

print("Handling final decision...\n")
handle_final_decision(evaluation)
print("\n" + "="*60)
print("✅ HIRING PROCESS COMPLETED")
print("="*60 + "\n")

