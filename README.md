# 🎙️ AgentForge: Your Next-Gen AI Technical Recruiter

Hiring for specialized roles like(e.g : MERN stack developers)is exhausting. Between sorting through hundreds of resumes, verifying GitHub links that might be empty, and playing phone tag with candidates, hours of productive time are lost every week. 

**AgentForge** is here to change that. Built with heart at **AgentForge Technologies**, it isn't just a script—it's a multi-agent AI partner that handles the heavy lifting of recruitment, so you can focus on the people, not the paperwork.

---

## ✨ Why AgentForge? (The Problem We're Solving)

Traditional recruitment is broken. Recruiters spend **~30% of their day** on administrative tasks and initial screening. Candidates often feel like their applications fall into a "black hole." 

**AgentForge humanizes the automation:**
*   **For Recruiters**: You get a curated shortlist of verified, high-scoring talent delivered straight to your Slack.
*   **For Candidates**: No more waiting. If the system likes a resume, the interview happens *now*. If a candidate is busy, it reaches out kindly via email to find a better time.

---

## ⚙️ What AgentForge Does For You

AgentForge coordinates a team of specialized AI "Agents" who work together like a specialized HR department:

### 1. The Expert Screening Agent
It doesn't just look for keywords; it understands context. It scans resumes for deep MERN stack experience, ensuring only the truly qualified move forward.

### 2. The Digital Detective (Background Verification)
Acts as a bridge of trust. It:
*   **Validates Identities**: Cross-references LinkedIn profiles.
*   **Checks Skills**: Actually looks into GitHub repositories to see real code, MERN projects, and how active the developer has been lately.
*   **Ensures Credibility**: Assigns a transparency score so you know who's the real deal.

### 3. The Friendly Interviewer (Vapi Voice AI)
This is where the magic happens. The system calls the candidate for a **human-like, 15-minute technical conversation**. 
*   It asks dynamic, project-based questions.
*   It listens, understands, and transcribes the entire chat.
*   If it can't reach them, it automatically sends a warm email with a link to book a slot that works for them.

### 4. The Decision Maker
After the interview, AgentForge synthesizes everything—the resume, the GitHub code, and the conversation—into a single, easy-to-read verdict on Slack.

---

## 🏗️ Inside the Engine

AgentForge is lean, powerful, and lives entirely in your terminal:

```bash
├── agents/             # The "Brains" of the system
│   ├── resume_screening_agent.py
│   ├── background_verification_agent.py
│   ├── calling_agent.py        # Voice & Vapi magic
│   ├── interview_question_agent.py
│   ├── final_decision_agent.py # The Slack updates
├── utils/              # The "Hands" (Parsing, Emails, Storage)
├── main.py             # 🚀 THE STARTING POINT
└── .env                # Your Secret Keys
```

---

## 🚦 Getting Started with AgentForge

We've made it as simple as possible to get up and running.

### 1. Clone the Repository
```bash
git clone https://github.com/Shivaraj-528/AI-pipeline-for-hiring.git
cd AGENT_FORGE
pip install -r requirements.txt
```

### 2. Set the Ground Rules
Create a `.env` file and provide the keys needed to work:
```env
OPENROUTER_API_KEY=your_key   # For AI logic
VAPI_API_KEY=your_key        # For voice calls
VAPI_ASSISTANT_ID=your_id
SLACK_WEBHOOK_URL=your_url    # For your updates
SENDER_EMAIL=your_email       # For candidate invites
SENDER_EMAIL_PASSWORD=your_app_password
```

### 3. Run the Pipeline
Place a resume in the `resumes/` folder and launch:
```bash
python main.py
```

---

## 🤝 Our Tech Stack
We believe in using the best tools for the job:
*   **Logic**: Llama 3 via OpenRouter.
*   **Voice**: Real-time telephony via Vapi.ai.
*   **Intelligence**: GitHub API and custom Parser.
*   **Heart**: Python.

---
<<<<<<< HEAD
*Created with ❤️ by Shivaraj Yelugodla *
=======
*Created with ❤️ by Shivaraj Yelugodla at AgentForge Technologies*
>>>>>>> 284781e (Update AgentForge to include Anti-Cheat, Salary Negotiation and comprehensive reports)
