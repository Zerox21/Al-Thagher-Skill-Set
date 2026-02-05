import smtplib
from email.message import EmailMessage
from flask import current_app

def send_email(to_email: str, subject: str, body: str, attachment_path: str | None = None):
    cfg = current_app.config
    if not cfg.get("SMTP_HOST") or not to_email:
        return False

    msg = EmailMessage()
    msg["From"] = cfg.get("SMTP_FROM") or cfg.get("SMTP_USER")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            data = f.read()
        msg.add_attachment(data, maintype="application", subtype="pdf", filename="report.pdf")

    with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"]) as s:
        s.starttls()
        if cfg.get("SMTP_USER"):
            s.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
        s.send_message(msg)
    return True
