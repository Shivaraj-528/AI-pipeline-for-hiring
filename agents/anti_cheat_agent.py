# agents/anti_cheat_agent.py
# ─────────────────────────────────────────────────────────────────────
# Anti-Cheat Detection Agent
# Detects if a candidate is reading AI-generated answers during
# a live phone interview using 3 techniques:
#   1. Response Latency Analysis — timing patterns
#   2. Unnatural Fluency Detection — too-perfect speech patterns
#   3. Curveball Questions — dynamic follow-ups to catch scripted answers
# Author  : Shivaraj Yelugodla  |  Date: 08-Mar-2026
# ─────────────────────────────────────────────────────────────────────

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


# ──────────────────────────────────────────────
# 1. RESPONSE LATENCY ANALYSIS
# ──────────────────────────────────────────────

def analyze_response_latency(transcript):
    """
    Analyze timing patterns in candidate responses.

    Genuine candidates:
      - Have natural pauses mid-thought ("um", "let me think")
      - Variable response times — some answers fast, some slow
      - Start answering quickly on topics they know

    AI-assisted candidates:
      - Consistent delay upfront (reading time from ChatGPT)
      - Unnaturally fluent delivery after the delay
      - No hesitation words at the start of answers

    Since Vapi transcripts don't include exact timestamps,
    we use proxy signals: word count consistency, filler word
    presence, and answer length variance.
    """
    if not transcript:
        return {"score": 0, "risk": "unknown", "details": []}

    lines = transcript.strip().splitlines()
    candidate_responses = []
    details = []

    for line in lines:
        line = line.strip()
        if line.lower().startswith("user:") or line.lower().startswith("candidate:"):
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            if len(content.split()) > 3:  # skip very short responses
                candidate_responses.append(content)

    if len(candidate_responses) < 2:
        return {"score": 50, "risk": "insufficient_data",
                "details": ["Too few responses to analyze latency patterns"]}

    # ── Metric 1: Response length variance ──
    # Genuine candidates have HIGH variance (some short, some long)
    # AI-read answers tend to have SIMILAR lengths (consistently long)
    word_counts = [len(r.split()) for r in candidate_responses]
    avg_words = sum(word_counts) / len(word_counts)
    variance = sum((w - avg_words) ** 2 for w in word_counts) / len(word_counts)
    std_dev = variance ** 0.5

    # Low std_dev = suspiciously uniform answer lengths
    if std_dev < 5 and avg_words > 30:
        details.append("⚠️ Suspiciously uniform answer lengths (std_dev={:.1f})".format(std_dev))
        length_score = 30  # high risk
    elif std_dev < 10:
        details.append("📊 Moderate answer length variation (std_dev={:.1f})".format(std_dev))
        length_score = 60
    else:
        details.append("✅ Natural answer length variation (std_dev={:.1f})".format(std_dev))
        length_score = 90

    # ── Metric 2: Filler word presence ──
    # Genuine speakers use "um", "uh", "like", "you know", "basically"
    # AI-read answers have ZERO filler words
    filler_words = ["um", "uh", "like", "you know", "basically", "actually",
                    "i mean", "let me think", "hmm", "well", "so basically",
                    "i think", "kind of", "sort of"]

    total_fillers = 0
    for response in candidate_responses:
        response_lower = response.lower()
        for filler in filler_words:
            total_fillers += response_lower.count(filler)

    fillers_per_response = total_fillers / len(candidate_responses) if candidate_responses else 0

    if fillers_per_response == 0 and avg_words > 25:
        details.append("⚠️ Zero filler words in long answers — unnatural speech pattern")
        filler_score = 25
    elif fillers_per_response < 0.5:
        details.append("📊 Very few filler words ({:.1f} per answer)".format(fillers_per_response))
        filler_score = 55
    else:
        details.append("✅ Natural filler word usage ({:.1f} per answer)".format(fillers_per_response))
        filler_score = 90

    # ── Metric 3: Immediate-start vs Hesitation-start ──
    # Genuine: starts with "So...", "I think...", "Well..."
    # AI-read: starts with direct technical statements
    hesitation_starters = ["so", "well", "i think", "um", "uh", "basically",
                           "yeah", "ok so", "let me", "hmm", "i would say",
                           "that's a good question", "right"]
    hesitant_starts = 0
    for response in candidate_responses:
        first_words = response.lower()[:30]
        if any(first_words.startswith(h) for h in hesitation_starters):
            hesitant_starts += 1

    hesitation_ratio = hesitant_starts / len(candidate_responses) if candidate_responses else 0

    if hesitation_ratio == 0 and len(candidate_responses) >= 3:
        details.append("⚠️ No natural hesitation at start of any answer")
        hesitation_score = 30
    elif hesitation_ratio < 0.3:
        details.append("📊 Low hesitation ratio ({:.0%})".format(hesitation_ratio))
        hesitation_score = 55
    else:
        details.append("✅ Natural hesitation patterns ({:.0%})".format(hesitation_ratio))
        hesitation_score = 90

    # ── Final latency score ──
    final_score = int((length_score * 0.3) + (filler_score * 0.4) + (hesitation_score * 0.3))

    if final_score >= 75:
        risk = "low"
    elif final_score >= 50:
        risk = "medium"
    else:
        risk = "high"

    return {"score": final_score, "risk": risk, "details": details}


# ──────────────────────────────────────────────
# 2. UNNATURAL FLUENCY DETECTION
# ──────────────────────────────────────────────

def detect_unnatural_fluency(transcript):
    """
    Detect if candidate answers are suspiciously well-structured.

    Genuine spoken answers:
      - Have grammar imperfections
      - Use informal/conversational tone
      - Include self-corrections ("I mean...", "wait, actually...")
      - Have shorter, fragmented sentences

    AI-generated answers (read aloud):
      - Perfect grammar, no mistakes
      - Textbook-style paragraph structure
      - Use formal transition words ("Furthermore", "Moreover")
      - Unnaturally long, well-organized responses
    """
    if not transcript:
        return {"score": 0, "risk": "unknown", "details": []}

    lines = transcript.strip().splitlines()
    candidate_responses = []
    details = []

    for line in lines:
        line = line.strip()
        if line.lower().startswith("user:") or line.lower().startswith("candidate:"):
            content = line.split(":", 1)[1].strip() if ":" in line else ""
            if len(content.split()) > 5:
                candidate_responses.append(content)

    if len(candidate_responses) < 2:
        return {"score": 50, "risk": "insufficient_data",
                "details": ["Too few responses for fluency analysis"]}

    # ── Metric 1: Formal academic language detection ──
    # These words are common in ChatGPT but rare in casual speech
    academic_markers = ["furthermore", "moreover", "additionally", "in conclusion",
                        "it is important to note", "it's worth mentioning",
                        "comprehensive", "utilize", "facilitate", "implement",
                        "leveraging", "paradigm", "robust", "scalable",
                        "in summary", "to summarize", "first and foremost",
                        "that being said", "with that in mind"]

    academic_count = 0
    for response in candidate_responses:
        response_lower = response.lower()
        for marker in academic_markers:
            if marker in response_lower:
                academic_count += 1

    if academic_count >= 4:
        details.append(f"⚠️ High academic language usage ({academic_count} markers) — ChatGPT-like")
        academic_score = 20
    elif academic_count >= 2:
        details.append(f"📊 Some formal language detected ({academic_count} markers)")
        academic_score = 55
    else:
        details.append(f"✅ Natural conversational tone ({academic_count} markers)")
        academic_score = 90

    # ── Metric 2: Self-correction presence ──
    # Genuine speakers correct themselves; AI readers don't
    correction_phrases = ["i mean", "wait", "actually", "sorry",
                          "let me rephrase", "what i meant", "no wait",
                          "correction", "i misspoke", "to be more precise"]

    corrections = 0
    for response in candidate_responses:
        response_lower = response.lower()
        for phrase in correction_phrases:
            if phrase in response_lower:
                corrections += 1

    if corrections == 0 and len(candidate_responses) >= 3:
        details.append("⚠️ Zero self-corrections in entire interview — unusually polished")
        correction_score = 35
    else:
        details.append(f"✅ Natural self-corrections detected ({corrections} instances)")
        correction_score = 90

    # ── Metric 3: Sentence complexity uniformity ──
    # Count sentences per response. AI answers tend to have
    # consistent multi-sentence structures (always 3-5 sentences).
    # Genuine answers vary wildly (1 sentence vs 6 sentences).
    sentence_counts = []
    for response in candidate_responses:
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        sentence_counts.append(len(sentences))

    if sentence_counts:
        sent_avg = sum(sentence_counts) / len(sentence_counts)
        sent_variance = sum((s - sent_avg) ** 2 for s in sentence_counts) / len(sentence_counts)
        sent_std = sent_variance ** 0.5

        if sent_std < 0.5 and sent_avg > 2:
            details.append("⚠️ All answers have near-identical sentence count — scripted")
            structure_score = 25
        elif sent_std < 1.0:
            details.append("📊 Low sentence structure variation")
            structure_score = 55
        else:
            details.append("✅ Varied answer structures — natural speech")
            structure_score = 90
    else:
        structure_score = 50

    # ── Final fluency score ──
    final_score = int((academic_score * 0.4) + (correction_score * 0.3) + (structure_score * 0.3))

    if final_score >= 75:
        risk = "low"
    elif final_score >= 50:
        risk = "medium"
    else:
        risk = "high"

    return {"score": final_score, "risk": risk, "details": details}


# ──────────────────────────────────────────────
# 3. CURVEBALL QUESTION GENERATOR
# ──────────────────────────────────────────────

def generate_curveball_questions(transcript, resume_text):
    """
    Generate dynamic follow-up 'curveball' questions based on the
    candidate's actual answers. These questions cannot be pre-prepared
    because they reference specific things the candidate said.

    Purpose: A candidate reading from ChatGPT can answer prepared questions,
    but they CANNOT anticipate follow-ups based on their own answers.

    Returns: List of 2-3 curveball questions + rationale.
    """
    if not transcript:
        return {"questions": [], "rationale": "No transcript available"}

    prompt = f"""You are an expert technical interviewer who suspects a candidate might be reading AI-generated answers during a phone interview.

Your task is to generate 2-3 "curveball" follow-up questions that would be IMPOSSIBLE to prepare for in advance. These questions must:

1. Reference SPECIFIC things the candidate said in their answers (quote them)
2. Ask them to go DEEPER on a detail they mentioned — if they made it up, they won't be able to elaborate
3. Include one question that introduces a DELIBERATE MISTAKE about something they said, to see if they correct it
4. Be practical and conversational (not accusatory)

CANDIDATE'S RESUME:
{resume_text[:500]}

INTERVIEW TRANSCRIPT:
{transcript}

---

Generate exactly 3 curveball questions in this format:
Curveball 1: <question>
Rationale: <why this catches cheaters>

Curveball 2: <question>
Rationale: <why this catches cheaters>

Curveball 3: <question>
Rationale: <why this catches cheaters>
"""

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        raw_output = response.choices[0].message.content.strip()

        # Parse curveball questions
        questions = []
        rationales = []
        for line in raw_output.split("\n"):
            line = line.strip()
            if line.startswith("Curveball"):
                q = line.split(":", 1)[1].strip() if ":" in line else line
                questions.append(q)
            elif line.startswith("Rationale"):
                r = line.split(":", 1)[1].strip() if ":" in line else line
                rationales.append(r)

        return {
            "questions": questions[:3],
            "rationales": rationales[:3],
            "raw_output": raw_output
        }

    except Exception as e:
        print(f"⚠️ Curveball generation failed: {e}")
        return {"questions": [], "rationales": [], "raw_output": str(e)}


# ──────────────────────────────────────────────
# COMBINED ANTI-CHEAT ANALYSIS
# ──────────────────────────────────────────────

def run_anti_cheat_analysis(transcript, resume_text=None):
    """
    Run the full anti-cheat analysis suite on an interview transcript.

    Returns a comprehensive report with:
    - Overall cheat risk: LOW / MEDIUM / HIGH
    - Latency analysis results
    - Fluency analysis results
    - Generated curveball questions for follow-up
    - Recommendation for HR
    """
    print("🛡️  Running anti-cheat analysis...")

    # 1. Response Latency Analysis
    print("   📊 Analyzing response latency patterns...")
    latency = analyze_response_latency(transcript)

    # 2. Unnatural Fluency Detection
    print("   🔍 Checking for unnatural fluency...")
    fluency = detect_unnatural_fluency(transcript)

    # 3. Curveball Questions
    print("   🎯 Generating curveball follow-up questions...")
    curveballs = generate_curveball_questions(transcript, resume_text or "")

    # ── Calculate overall risk ──
    avg_score = (latency["score"] + fluency["score"]) / 2

    if avg_score >= 75:
        overall_risk = "LOW"
        recommendation = "Candidate appears genuine. Proceed with confidence."
        risk_emoji = "✅"
    elif avg_score >= 50:
        overall_risk = "MEDIUM"
        recommendation = "Some suspicious patterns detected. Consider asking curveball questions in a follow-up round."
        risk_emoji = "⚠️"
    else:
        overall_risk = "HIGH"
        recommendation = "Strong indicators of AI-assisted answering. Recommend a live video follow-up with curveball questions."
        risk_emoji = "🚨"

    report = {
        "overall_risk": overall_risk,
        "overall_score": int(avg_score),
        "recommendation": recommendation,
        "risk_emoji": risk_emoji,
        "latency_analysis": latency,
        "fluency_analysis": fluency,
        "curveball_questions": curveballs,
    }

    return report
