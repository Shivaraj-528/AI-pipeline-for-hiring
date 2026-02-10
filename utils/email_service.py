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


def send_call_booking_email(candidate_email, candidate_name="Candidate"):
    """
    Send email to candidate who didn't answer the phone call,
    with a link to book a convenient time for the interview.
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email credentials not configured.")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Interview Call - Schedule at Your Convenience | Arya Stack Technologies"
    msg["From"] = SENDER_EMAIL
    msg["To"] = candidate_email

    # HTML email for better formatting
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 30px; 
            background-color: #4CAF50; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Arya Stack Technologies</h2>
            <p>MERN Stack Developer - Interview Invitation</p>
        </div>
        
        <div class="content">
            <p>Dear {candidate_name},</p>
            
            <p>Thank you for applying for the <strong>MERN Stack Developer</strong> position at Arya Stack Technologies!</p>
            
            <p>We recently attempted to reach you via phone for a technical interview, but were unable to connect. We understand that you may have been busy or unavailable at that time.</p>
            
            <p><strong>Good news!</strong> You can now schedule the interview at a time that works best for you.</p>
            
            <p style="text-align: center;">
                <a href="https://calendly.com/aryastack/interview" class="button">📅 Book Your Interview Slot</a>
            </p>
            
            <p><strong>What to expect:</strong></p>
            <ul>
                <li>Duration: 15-20 minutes</li>
                <li>Format: Phone interview with our AI interviewer</li>
                <li>Focus: MERN Stack technical questions based on your resume</li>
                <li>Topics: MongoDB, Express.js, React.js, Node.js, and your projects</li>
            </ul>
            
            <p><strong>Important:</strong> Please book your slot within the next 48 hours to keep your application active.</p>
            
            <p>If you have any questions or need assistance, feel free to reply to this email.</p>
            
            <p>We look forward to speaking with you!</p>
            
            <p>Best regards,<br>
            <strong>HR Team</strong><br>
            Arya Stack Technologies<br>
            Email: {SENDER_EMAIL}</p>
        </div>
        
        <div class="footer">
            <p>This is an automated email from Arya Stack Technologies AI Hiring System.</p>
            <p>If you did not apply for this position, please disregard this email.</p>
        </div>
    </div>
</body>
</html>
"""

    # Plain text alternative
    plain_text = f"""
Dear {candidate_name},

Thank you for applying for the MERN Stack Developer position at Arya Stack Technologies!

We recently attempted to reach you via phone for a technical interview, but were unable to connect. We understand that you may have been busy or unavailable at that time.

GOOD NEWS! You can now schedule the interview at a time that works best for you.

📅 Book Your Interview Slot:
https://calendly.com/aryastack/interview

What to expect:
- Duration: 15-20 minutes
- Format: Phone interview with our AI interviewer
- Focus: MERN Stack technical questions based on your resume
- Topics: MongoDB, Express.js, React.js, Node.js, and your projects

IMPORTANT: Please book your slot within the next 48 hours to keep your application active.

If you have any questions or need assistance, feel free to reply to this email.

We look forward to speaking with you!

Best regards,
HR Team
Arya Stack Technologies
Email: {SENDER_EMAIL}

---
This is an automated email from Arya Stack Technologies AI Hiring System.
If you did not apply for this position, please disregard this email.
"""

    msg.set_content(plain_text)
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Call booking email sent to {candidate_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send call booking email: {e}")
        return False
