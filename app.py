import streamlit as st
import os

from agents.calling_agent import start_interview_call
from agents.resume_screening_agent import screen_resume
from agents.interview_question_agent import generate_interview_questions
from agents.interview_evaluation_agent import evaluate_interview
from agents.final_decision_agent import handle_final_decision
from utils.resume_parser import extract_resume_text

st.set_page_config(page_title="Arya Stack Hiring AI", layout="centered")

st.title("🤖 Arya Stack Technologies – AI Hiring Agent")

st.markdown("Upload resume and start AI-powered interview")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

phone_number = st.text_input("Candidate Phone Number", "+91")

if uploaded_file:
    with open("temp_resume.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.success("Resume uploaded successfully")

    if st.button("Start Interview"):
        with st.spinner("Processing resume..."):
            resume_text = extract_resume_text("temp_resume.pdf")
            screening_result = screen_resume(resume_text)
            questions = generate_interview_questions(resume_text)

        st.info("Calling candidate...")
        start_interview_call(phone_number, questions)

        st.success("Interview call started")

        st.info("Waiting for interview transcript...")

        transcript_path = "demo_assets/interview_transcript.txt"
        if os.path.exists(transcript_path):
            transcript = open(transcript_path).read()
            evaluation = evaluate_interview(resume_text, transcript)
            handle_final_decision(evaluation)
            st.success("Interview evaluated & HR notified")
