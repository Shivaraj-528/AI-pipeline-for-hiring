import os
from dotenv import load_dotenv

load_dotenv()  # this now works because it's a real file

print("Sender email:", os.getenv("SENDER_EMAIL"))
print("Email password exists:", bool(os.getenv("SENDER_EMAIL_PASSWORD")))
