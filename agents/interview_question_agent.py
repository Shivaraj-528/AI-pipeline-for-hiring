# agents/interview_question_agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def generate_interview_questions(resume_text):
    prompt = f"""
You are a technical interviewer at Arya Stack Technologies.

Role: MERN Stack Developer

Task:
Based on the candidate resume below, generate 5 interview questions.
The questions should:
- Focus on MERN stack (MongoDB, Express, React, Node.js)
- Be practical and project-based
- Avoid basic theory questions

Resume:
{resume_text}

Return the questions as a numbered list.
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()
