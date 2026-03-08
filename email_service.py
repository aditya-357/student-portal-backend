import smtplib
import os
from email.message import EmailMessage

EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()
