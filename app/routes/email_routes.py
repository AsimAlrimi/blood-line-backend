# app/routes/email_routes.py
from flask import Blueprint, request, jsonify
from app.services.email_service import send_email

email_bp = Blueprint('email_bp', __name__)

@email_bp.route('/test', methods=["POST"])
def test_email():
    """Endpoint to test sending an email."""
    data = request.get_json()
    recipient_email = data['email']
    subject = "Registration Status Update"
    body = "Your registration has been approved."
    
    send_email(subject, [recipient_email], body)
    return jsonify({"msg": "Notification email sent!"}), 200
