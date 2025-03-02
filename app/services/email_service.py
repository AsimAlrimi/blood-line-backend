from flask_mail import Message

def send_email(subject, recipients, body):
    from app import mail  # Lazy import to avoid circular import
    msg = Message(subject, recipients=recipients, body=body)
    mail.send(msg)