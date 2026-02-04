import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from pathlib import Path

# Load .env safely
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_EMAIL_PASSWORD")


def send_selection_email(candidate_email, candidate_name="Candidate"):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email credentials not configured.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Congratulations! Interview Result – Arya Stack Technologies"
    msg["From"] = SENDER_EMAIL
    msg["To"] = candidate_email

    msg.set_content(f"""
Dear {candidate_name},

Congratulations!

We are pleased to inform you that you have successfully cleared the interview rounds for the MERN Stack Developer position at Arya Stack Technologies.

Our HR team will reach out to you shortly with the next steps.

We look forward to working with you.

Best regards,
HR Team
Arya Stack Technologies
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"Selection email sent to {candidate_email}")

    except Exception as e:
        print("Failed to send email:", e)
