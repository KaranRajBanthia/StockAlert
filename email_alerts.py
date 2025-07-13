
import smtplib
from email.mime.text import MIMEText
import os

def send_email_alert(alert_data):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    recipient = os.environ.get("EMAIL_USER")

    subject = "📈 Stock Alert Triggered"
    body = ""
    for alert in alert_data:
        body += f"{alert['Ticker']} - {alert['Alert']}\n\n"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)
