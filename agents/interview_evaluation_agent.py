# agents/interview_evaluation_agent.py
# ─────────────────────────────────────────────────────────────────────
# Stage 5 — Interview Evaluation Agent
# Two-phase scoring: Python deterministically counts Q&A turns (ground truth),
# then LLM (Llama 3) judges answer quality. Pass = ≥2 perfect answers.
# Author  : Shivaraj Yelugodla  |  Date: 07-Mar-2026
# ─────────────────────────────────────────────────────────────────────

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def count_questions_in_transcript(transcript):
    """
    Count the number of complete questions the AI interviewer
    actually asked in the transcript. Uses Python — ground truth,
    not LLM inference — so the count is always accurate.
    """
    questions_asked = 0
    lines = transcript.strip().splitlines()

    for line in lines:
        line = line.strip()
        # Only look at AI/Interviewer lines
        if not line.lower().startswith("ai:"):
            continue

        content = line[3:].strip()  # Remove "AI:" prefix

        # Skip very short lines or incomplete sentences (cut-off mid-call)
        if len(content) < 30:
            continue

        # Count lines that contain a question mark — these are actual questions
        # Also require the line to be substantive (not just filler like "Thank you for your response")
        filler_phrases = ["thank you", "great", "let's move on", "okay", "good", "understood"]
        is_filler_only = any(content.lower().startswith(p) for p in filler_phrases) and "?" not in content

        if "?" in content and not is_filler_only:
            questions_asked += 1

    return questions_asked


def count_candidate_turns(transcript):
    """
    Count the number of lines where the candidate actually responded
    with something meaningful (not just "Hello", "Yes", "No", etc.).
    """
    meaningful_turns = 0
    lines = transcript.strip().splitlines()
    filler_responses = {"hello", "yes", "no", "okay", "ok", "hi", "sure", "alright", "yeah"}

    for line in lines:
        line = line.strip()
        if not line.lower().startswith("user:"):
            continue
        content = line[5:].strip()
        # Meaningful if more than 5 words and not just a filler word
        words = content.split()
        if len(words) > 5 and content.lower().strip("?.!") not in filler_responses:
            meaningful_turns += 1

    return meaningful_turns


def evaluate_interview(resume_text, interview_transcript):
    # --- Step 1: Count questions using Python (ground truth) ---
    questions_asked = count_questions_in_transcript(interview_transcript)
    meaningful_turns = count_candidate_turns(interview_transcript)

    print(f"   📊 Questions detected in transcript: {questions_asked}")
    print(f"   📊 Meaningful candidate responses: {meaningful_turns}")

    # --- Step 2: Ask LLM to evaluate quality of answers only ---
    prompt = f"""You are a strict technical interviewer evaluating a candidate for a MERN Stack Developer role at AgentForge Technologies.

Your evaluation must be based STRICTLY on the interview transcript below. Do NOT use the resume to boost the score.

IMPORTANT — The following counts have already been determined by analysing the transcript programmatically. You MUST use these exact numbers in your output:
- Total questions the interviewer asked: {questions_asked}
- Total meaningful responses from the candidate: {meaningful_turns}

INTERVIEW TRANSCRIPT:
{interview_transcript}

---

EVALUATION RULES (follow exactly):

Step 1 — Accept the pre-counted questions:
Questions Asked = {questions_asked}  ← USE THIS EXACT NUMBER, do not recount.

Step 2 — Count Perfect Answers:
From the {questions_asked} questions above, count how many the candidate answered with a CLEAR, CORRECT, and RELEVANT technical answer.
A "perfect answer" means:
- The candidate directly addressed the question asked
- The answer contains real technical substance (not vague, not "I don't know", not off-topic)
- The answer demonstrates understanding of MERN stack concepts

Step 3 — Apply Pass/Fail Rule:
- If the candidate gave 2 or more perfect answers → Decision: Pass
- If the candidate gave fewer than 2 perfect answers → Decision: Fail
- If questions_asked is 0, or the transcript is too short → Decision: Fail

Step 4 — Calculate Score:
If {questions_asked} > 0: Score = (perfect_answers / {questions_asked}) * 100
If {questions_asked} == 0: Score = 0

---

Respond in EXACTLY this format (no preamble, no extra text):

Questions Asked: {questions_asked}
Perfect Answers: <number>
Score: <number out of 100>
Decision: <Pass / Fail>
Reason: <2-3 sentences explaining the decision based strictly on the transcript>
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content.strip()
