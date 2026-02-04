# agents/resume_screening_agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def screen_resume(resume_text):
    prompt = f"""
You are an HR recruiter at Arya Stack Technologies.

Job Role: MERN Stack Developer

Job Requirements:
- MongoDB
- Express.js
- React.js
- Node.js
- Hands-on project experience

Task:
Based on the resume below, decide whether the candidate is QUALIFIED or NOT QUALIFIED.
Give a short reason.

Resume:
{resume_text}

Respond strictly in this format:
Decision: <Qualified / Not Qualified>
Reason: <one short sentence>
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
