import smtplib
from email.message import EmailMessage
from config import Config


def _send_email(to_address, subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)


def _log(cursor, complaint_id, recipient_id, channel, event, status, message):
    cursor.execute(
        """INSERT INTO notifications
           (complaint_id, recipient_id, channel, event, status, message)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (complaint_id, recipient_id, channel, event, status, message),
    )


def send_notification(cursor, complaint_id, recipient_id, event, message):
    # A notification problem must never break the main action
    try:
        cursor.execute("SELECT name, email FROM users WHERE id = %s", (recipient_id,))
        user = cursor.fetchone()
        if not user:
            return

        # Channel 1: Email
        if Config.EMAIL_ENABLED:
            try:
                _send_email(user["email"], f"SmartResolve: {event}", message)
                email_status = "Sent"
            except Exception as error:
                print(f"[Notification] Email failed: {error}")
                email_status = "Failed"
        else:
            email_status = "Skipped"
        _log(cursor, complaint_id, recipient_id, "Email", event, email_status, message)

        # Channel 2: WhatsApp (mock - only prints and logs)
        print(f"[Mock WhatsApp] To {user['name']}: {message}")
        _log(cursor, complaint_id, recipient_id, "WhatsApp", event, "Mock", message)

    except Exception as error:
        print(f"[Notification] Could not send notification: {error}")