"""
utils/db.py
-----------
Supabase (PostgreSQL) integration for AgentForge.
Uses psycopg2 with a direct Postgres connection via the credentials in .env

Tables managed here:
  - candidates           → master record per candidate
  - screening_results    → resume screening output
  - background_checks    → verification scores
  - interview_sessions   → call info + transcript
  - evaluation_results   → final score + decision
"""

from typing import Optional
import os
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


# ──────────────────────────────────────────────
# Connection
# ──────────────────────────────────────────────

def get_connection():
    """
    Return a new psycopg2 connection to Supabase (Postgres).
    Tries the direct DB host first; falls back to the session pooler
    if the direct host is unreachable.
    """
    direct_host   = os.getenv("DB_HOST")
    pooler_host   = os.getenv("DB_POOLER_HOST", direct_host)
    db_name       = os.getenv("DB_NAME", "postgres")
    db_user       = os.getenv("DB_USER", "postgres")
    db_password   = os.getenv("DB_PASSWORD")
    db_port       = int(os.getenv("DB_PORT", 5432))

    for host in [direct_host, pooler_host]:
        if not host:
            continue
        try:
            conn = psycopg2.connect(
                host=host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=db_port,
                sslmode="require",
                connect_timeout=8,
            )
            return conn
        except Exception as e:
            last_err = e  # try next host
            continue

    raise last_err  # both hosts failed


def test_connection():
    """Quick connectivity test. Returns True/False."""
    try:
        conn = get_connection()
        conn.close()
        print("✅ Supabase connection successful!")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


# ──────────────────────────────────────────────
# Schema bootstrap  (run once on first deploy)
# ──────────────────────────────────────────────

def init_tables():
    """
    Create all necessary tables if they don't already exist.
    Safe to call on every startup.
    """
    ddl = """
    -- Master candidate record
    CREATE TABLE IF NOT EXISTS candidates (
        id              SERIAL PRIMARY KEY,
        name            TEXT,
        email           TEXT UNIQUE,
        phone           TEXT,
        resume_text     TEXT,
        linkedin_url    TEXT,
        github_username TEXT,
        created_at      TIMESTAMPTZ DEFAULT NOW()
    );

    -- Resume screening outcome
    CREATE TABLE IF NOT EXISTS screening_results (
        id              SERIAL PRIMARY KEY,
        candidate_id    INT REFERENCES candidates(id) ON DELETE CASCADE,
        decision        TEXT NOT NULL,          -- 'Qualified' | 'Not Qualified'
        reason          TEXT,
        raw_output      TEXT,
        screened_at     TIMESTAMPTZ DEFAULT NOW()
    );

    -- Background verification
    CREATE TABLE IF NOT EXISTS background_checks (
        id                  SERIAL PRIMARY KEY,
        candidate_id        INT REFERENCES candidates(id) ON DELETE CASCADE,
        credibility_score   INT,
        status              TEXT,               -- 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'UNVERIFIED'
        recommendation      TEXT,
        email_valid         BOOLEAN,
        email_confidence    INT,
        linkedin_found      BOOLEAN,
        linkedin_confidence INT,
        github_found        BOOLEAN,
        github_repos        INT,
        github_mern_projects INT,
        issues              TEXT[],
        verified_at         TIMESTAMPTZ DEFAULT NOW()
    );

    -- Interview call session
    CREATE TABLE IF NOT EXISTS interview_sessions (
        id                  SERIAL PRIMARY KEY,
        candidate_id        INT REFERENCES candidates(id) ON DELETE CASCADE,
        call_id             TEXT,               -- Vapi call ID
        phone_number        TEXT,
        call_status         TEXT,               -- 'completed' | 'no-answer' | 'failed'
        questions_asked     TEXT,
        transcript          TEXT,
        duration_seconds    INT,
        called_at           TIMESTAMPTZ DEFAULT NOW()
    );

    -- Final evaluation + decision
    CREATE TABLE IF NOT EXISTS evaluation_results (
        id                  SERIAL PRIMARY KEY,
        candidate_id        INT REFERENCES candidates(id) ON DELETE CASCADE,
        questions_asked     INT,
        perfect_answers     INT,
        score               NUMERIC(5,2),
        decision            TEXT NOT NULL,      -- 'Pass' | 'Fail'
        reason              TEXT,
        raw_output          TEXT,
        slack_notified      BOOLEAN DEFAULT FALSE,
        email_sent          BOOLEAN DEFAULT FALSE,
        evaluated_at        TIMESTAMPTZ DEFAULT NOW()
    );
    """

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(ddl)
        conn.commit()
        cur.close()
        print("✅ Supabase tables initialised.")
    except Exception as e:
        print(f"❌ Failed to initialise tables: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# Candidate  (upsert by email)
# ──────────────────────────────────────────────

def upsert_candidate(name=None, email=None, phone=None, resume_text=None,
                     linkedin_url=None, github_username=None) -> Optional[int]:
    """
    Insert or update a candidate row.
    Returns the candidate's integer id, or None on failure.
    """
    sql = """
    INSERT INTO candidates (name, email, phone, resume_text, linkedin_url, github_username)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (email) DO UPDATE SET
        name            = EXCLUDED.name,
        phone           = EXCLUDED.phone,
        resume_text     = EXCLUDED.resume_text,
        linkedin_url    = EXCLUDED.linkedin_url,
        github_username = EXCLUDED.github_username
    RETURNING id;
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, (name, email, phone, resume_text, linkedin_url, github_username))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        candidate_id = row[0] if row else None
        print(f"📁 Candidate saved (id={candidate_id})")
        return candidate_id
    except Exception as e:
        print(f"❌ upsert_candidate failed: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_candidate_by_email(email: str) -> Optional[dict]:
    """Look up a candidate by email. Returns a dict or None."""
    sql = "SELECT * FROM candidates WHERE email = %s LIMIT 1;"
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, (email,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ get_candidate_by_email failed: {e}")
        return None
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# Screening Result
# ──────────────────────────────────────────────

def save_screening_result(candidate_id: int, raw_output: str):
    """Parse and save the screening agent's raw output."""
    decision = "Not Qualified"
    reason = ""
    for line in raw_output.splitlines():
        if line.startswith("Decision:"):
            decision = line.split(":", 1)[1].strip()
        elif line.startswith("Reason:"):
            reason = line.split(":", 1)[1].strip()

    sql = """
    INSERT INTO screening_results (candidate_id, decision, reason, raw_output)
    VALUES (%s, %s, %s, %s);
    """
    _execute(sql, (candidate_id, decision, reason, raw_output),
             success_msg="📋 Screening result saved.")


# ──────────────────────────────────────────────
# Background Verification
# ──────────────────────────────────────────────

def save_background_check(candidate_id: int, verification_result: dict):
    """Save the output from background_verification_agent.verify_background()."""
    checks = verification_result.get("checks", {})
    email_check = checks.get("email", {})
    linkedin_check = checks.get("linkedin", {})
    github_check = checks.get("github", {})

    sql = """
    INSERT INTO background_checks (
        candidate_id, credibility_score, status, recommendation,
        email_valid, email_confidence,
        linkedin_found, linkedin_confidence,
        github_found, github_repos, github_mern_projects,
        issues
    ) VALUES (%s,%s,%s,%s, %s,%s, %s,%s, %s,%s,%s, %s);
    """
    values = (
        candidate_id,
        verification_result.get("credibility_score"),
        verification_result.get("status"),
        verification_result.get("recommendation"),
        email_check.get("valid"),
        email_check.get("confidence"),
        linkedin_check.get("found"),
        linkedin_check.get("confidence"),
        github_check.get("found"),
        github_check.get("public_repos"),
        github_check.get("mern_projects"),
        verification_result.get("issues", []),
    )
    _execute(sql, values, success_msg="🔍 Background check saved.")


# ──────────────────────────────────────────────
# Interview Session
# ──────────────────────────────────────────────

def save_interview_session(candidate_id: int, call_id: str, phone_number: str,
                           questions: str, transcript: str = None,
                           call_status: str = "completed", duration_seconds: int = None):
    """Save a Vapi interview call session."""
    sql = """
    INSERT INTO interview_sessions
        (candidate_id, call_id, phone_number, call_status, questions_asked, transcript, duration_seconds)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    _execute(sql, (candidate_id, call_id, phone_number, call_status,
                   questions, transcript, duration_seconds),
             success_msg="📞 Interview session saved.")


# ──────────────────────────────────────────────
# Evaluation Result
# ──────────────────────────────────────────────

def save_evaluation_result(candidate_id: int, raw_output: str,
                           slack_notified=False, email_sent=False):
    """Parse and save the final LLM evaluation output."""
    parsed = _parse_evaluation(raw_output)
    sql = """
    INSERT INTO evaluation_results
        (candidate_id, questions_asked, perfect_answers, score, decision,
         reason, raw_output, slack_notified, email_sent)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
    """
    values = (
        candidate_id,
        parsed["questions_asked"],
        parsed["perfect_answers"],
        parsed["score"],
        parsed["decision"],
        parsed["reason"],
        raw_output,
        slack_notified,
        email_sent,
    )
    _execute(sql, values, success_msg="📊 Evaluation result saved.")


def _parse_evaluation(raw: str) -> dict:
    """Parse structured evaluation text into a dict."""
    result = {
        "questions_asked": None,
        "perfect_answers": None,
        "score": None,
        "decision": "Fail",
        "reason": "",
    }
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("Questions Asked:"):
            try:
                result["questions_asked"] = int(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                pass
        elif line.startswith("Perfect Answers:"):
            try:
                result["perfect_answers"] = int(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                pass
        elif line.startswith("Score:"):
            try:
                result["score"] = float(line.split(":", 1)[1].strip().split()[0])
            except Exception:
                pass
        elif line.startswith("Decision:"):
            result["decision"] = line.split(":", 1)[1].strip()
        elif line.startswith("Reason:"):
            result["reason"] = line.split(":", 1)[1].strip()
    return result


# ──────────────────────────────────────────────
# Legacy / compatibility shim
# (replaces utils/json_store.store_candidate_json)
# ──────────────────────────────────────────────

def store_candidate_result(candidate_data: dict):
    """
    Generic save used by final_decision_agent.
    Expects keys: decision, evaluation_summary, remarks (optional).
    Falls back gracefully if candidate_id unavailable.
    """
    candidate_id = candidate_data.get("candidate_id")
    raw_output = candidate_data.get("evaluation_summary", "")
    slack_notified = candidate_data.get("slack_notified", False)
    email_sent = candidate_data.get("email_sent", False)

    if candidate_id:
        save_evaluation_result(candidate_id, raw_output, slack_notified, email_sent)
    else:
        # Minimal insert without foreign-key link
        sql = """
        INSERT INTO evaluation_results (decision, reason, raw_output, slack_notified, email_sent)
        VALUES (%s, %s, %s, %s, %s);
        """
        decision = candidate_data.get("decision", "Fail")
        reason = candidate_data.get("remarks", "")
        _execute(sql, (decision, reason, raw_output, slack_notified, email_sent),
                 success_msg="📁 Candidate result stored in Supabase.")


# ──────────────────────────────────────────────
# Read helpers (for dashboard / reporting)
# ──────────────────────────────────────────────

def get_all_candidates() -> list[dict]:
    """Return all candidates with their latest evaluation decision."""
    sql = """
    SELECT
        c.id, c.name, c.email, c.phone, c.github_username, c.created_at,
        er.decision, er.score, er.evaluated_at
    FROM candidates c
    LEFT JOIN LATERAL (
        SELECT decision, score, evaluated_at
        FROM evaluation_results
        WHERE candidate_id = c.id
        ORDER BY evaluated_at DESC
        LIMIT 1
    ) er ON TRUE
    ORDER BY c.created_at DESC;
    """
    return _fetch_all(sql)


def get_pipeline_stats() -> dict:
    """Return aggregate stats for the dashboard."""
    sql = """
    SELECT
        COUNT(DISTINCT c.id)                                        AS total_candidates,
        COUNT(DISTINCT sr.candidate_id)
            FILTER (WHERE sr.decision ILIKE '%qualified%'
                    AND sr.decision NOT ILIKE '%not%')              AS passed_screening,
        COUNT(DISTINCT bc.candidate_id)
            FILTER (WHERE bc.credibility_score >= 70)               AS passed_verification,
        COUNT(DISTINCT er.candidate_id)
            FILTER (WHERE er.decision ILIKE 'pass')                 AS final_passed,
        COUNT(DISTINCT er.candidate_id)
            FILTER (WHERE er.decision ILIKE 'fail')                 AS final_failed
    FROM candidates c
    LEFT JOIN screening_results  sr ON sr.candidate_id = c.id
    LEFT JOIN background_checks  bc ON bc.candidate_id = c.id
    LEFT JOIN evaluation_results er ON er.candidate_id = c.id;
    """
    rows = _fetch_all(sql)
    return rows[0] if rows else {}


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _execute(sql: str, values: tuple, success_msg: str = ""):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()
        cur.close()
        if success_msg:
            print(success_msg)
    except Exception as e:
        print(f"❌ DB write failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def _fetch_all(sql: str, values: tuple = ()) -> list[dict]:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, values)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows
    except Exception as e:
        print(f"❌ DB read failed: {e}")
        return []
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# Legacy transcript save (called from webhook_server)
# ──────────────────────────────────────────────

def save_transcript(data: dict):
    """
    Called from webhook_server.py.
    data keys: name, email, role, duration, transcript,
               interview_score, sentiment_score, status
    """
    # Ensure candidate exists
    candidate_id = upsert_candidate(
        name=data.get("name"),
        email=data.get("email"),
    )
    if candidate_id:
        save_interview_session(
            candidate_id=candidate_id,
            call_id="webhook",
            phone_number="",
            questions="",
            transcript=data.get("transcript"),
            call_status=data.get("status", "completed"),
            duration_seconds=data.get("duration"),
        )