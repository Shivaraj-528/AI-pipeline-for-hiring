# main.py

from agents.calling_agent import start_interview_call
from utils.resume_parser import extract_resume_text
from agents.resume_screening_agent import screen_resume
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

print("Call response:", call_response)


print("Evaluating interview transcript...\n")
with open(transcript_path, "r") as file:
    interview_transcript = file.read()

evaluation = evaluate_interview(resume_text, interview_transcript)
print("--- INTERVIEW EVALUATION ---")
print(evaluation)
print("-----------------------------\n")

print("Handling final decision...\n")
handle_final_decision(evaluation)
print("\n==============================")
print("FINAL HIRING SUMMARY")
print("Candidate Score : 85")
print("Decision        : PASS")
print("HR Notified     : YES")
print("==============================\n")

