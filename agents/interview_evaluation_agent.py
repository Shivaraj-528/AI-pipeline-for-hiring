# agents/interview_evaluation_agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def evaluate_interview(resume_text, interview_transcript):
    prompt = f"""
You are a senior technical interviewer at Arya Stack Technologies.

Role: MERN Stack Developer

Task:
Evaluate the candidate based on:
- Technical understanding of MERN stack
- Project explanation
- Communication clarity

Resume:
{resume_text}

Interview Transcript:
{interview_transcript}

Give your evaluation in the following format ONLY:

Score: <number out of 100>
Decision: <Pass / Fail>
Reason: <short explanation>
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
