import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash
from app.models import Donor, StaffMember, Admin, Manager
from app import db
from app.models.blood_bank import BloodBank
from app.models.faq import FAQ
from app.models.registration_request import RegistrationRequest
from app.services.email_service import send_email

admin_bp = Blueprint('admin_bp', __name__)

def generate_numeric_password():
    return str(random.randint(100000, 999999))

# Desktop 1
@admin_bp.route('/admin/get_registration_requests', methods=['GET'])
@jwt_required()
def get_registration_requests():
    # Admin-specific logic to fetch all pending requests
    pending_requests = RegistrationRequest.query.filter_by(request_status="Pending").all()

    current_user_id = get_jwt_identity()

    # Check if the current user is a donor
    admin = Admin.query.filter_by(id=current_user_id).first()
    if not admin:
        return jsonify({"error": "Unauthorized access."}), 403

    
    requests_data = [
        {
            'request_id': req.request_id,
            'organization_name': req.organization_name,
            'latitude': req.latitude,  # Reflecting the replacement of organization_address
            'longitude': req.longitude,  # Reflecting the replacement of organization_address
            'contact_info': req.contact_info,
            'start_hour': req.start_hour,  # Reflecting the replacement of operating_hours_m
            'close_hour': req.close_hour,  # Reflecting the replacement of operating_hours_m
            'manager_name': req.manager_name,
            'manager_email': req.manager_email
        }
        for req in pending_requests
    ]
    
    return jsonify(requests_data), 200



# Desktop 2
@admin_bp.route('/admin/update_registration_request', methods=['POST'])
@jwt_required()
def update_registration_request():
    data = request.get_json()
    request_id = data.get('request_id')
    new_status = data.get('status')  # Accept or Reject
    adim_message_body = data.get('adim_message_body')

    current_user_id = get_jwt_identity()

    # Check if the current user is a donor
    admin = Admin.query.filter_by(id=current_user_id).first()
    if not admin:
        return jsonify({"error": "Unauthorized access."}), 403

    if request_id is None or new_status is None:
        return jsonify({"msg": "Missing request_id or status"}), 400

    req = RegistrationRequest.query.get(request_id)
    
    if not req:
        return jsonify({"msg": "Request not found"}), 404

    if new_status == "Accept":
        password = generate_numeric_password()

        accept_message = (
            "Congratulations! Your registration request has been accepted.\n\n"
            "You can now access the Blood Line platform as a manager. \n"
            f"Please use the provided password to log in: {password} \n\n"
            f"Admin Message: {adim_message_body} \n\n"
            "Thank you for joining our efforts in making blood donation more accessible."
        )
        
        # Try to send the email and check for errors
        email_response = send_email("Registration Status Update", [req.manager_email], accept_message)
        if email_response:
            return jsonify(email_response), 500

        new_blood_bank = BloodBank(
            name=req.organization_name,
            latitude=req.latitude,  # Using latitude from the request
            longitude=req.longitude,  # Using longitude from the request
            phone_number=req.contact_info,
            email="",  # Email is still empty as per the original code
            start_hour=req.start_hour,  # Using start_hour from the request
            close_hour=req.close_hour  # Using close_hour from the request
        )
        
        db.session.add(new_blood_bank)
        db.session.flush()  # Get blood_bank_id

        new_manager_id = (
            Manager.query.filter(Manager.id.between(200000, 299999))
            .order_by(Manager.id.desc())
            .first()
        )
        next_manager_id = (new_manager_id.id + 1) if new_manager_id else 200000

        new_manager = Manager(
            id=next_manager_id,
            username=req.manager_name,
            email=req.manager_email,
            password=generate_password_hash(password),
            blood_bank_id=new_blood_bank.blood_bank_id
        )
        db.session.add(new_manager)


        req.request_status = "Approved"
        try:
            db.session.commit()
            return jsonify({
                "msg": "Request accepted and manager/organization added successfully!",
                "password": password
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Database error occurred", "error": str(e)}), 500

    elif new_status == "Reject":
        req.request_status = "Rejected"

        reject_message = (
            "We regret to inform you that your registration request has been rejected.\n\n"
            f"{adim_message_body}\n\n"
            "If you have any questions or need further assistance, please don't hesitate "
            "to contact our support team for clarification or to address any concerns."
        )
        
        # Try to send the email and check for errors
        email_response = send_email("Registration Status Update", [req.manager_email], reject_message)
        if email_response:
            return jsonify(email_response), 500

        try:
            db.session.commit()
            return jsonify({"msg": "Request rejected!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"msg": "Database error occurred", "error": str(e)}), 500
    else:
        return jsonify({"msg": "Invalid status provided!"}), 400


@admin_bp.route('/admin/add_faq', methods=['POST'])
@jwt_required()
def add_faq():

    admin_id = get_jwt_identity()

    adnin = Admin.query.get(admin_id)

    if not adnin:
        return jsonify({"error": "Unauthorized access."}), 403

    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')

    # Validate input
    if not question or not answer:
        return jsonify({"error": "Question and answer are required"}), 400

    try:
        # Create a new FAQ instance
        new_faq = FAQ(
            question=question,
            answer=answer,
            created_by=admin_id
        )

        # Save to database
        db.session.add(new_faq)
        db.session.commit()

        return jsonify({
            "message": "FAQ added successfully",
            "faq": {
                "id": new_faq.faq_id,
                "question": new_faq.question,
                "answer": new_faq.answer,
                "created_by": admin_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@admin_bp.route('/delete_faq/<int:faq_id>', methods=['DELETE'])
@jwt_required()
def delete_faq(faq_id):

    admin_id = get_jwt_identity()

    adnin = Admin.query.get(admin_id)

    if not adnin:
        return jsonify({"error": "Unauthorized access."}), 403
    
    try:
        # Find the FAQ by its ID
        faq = FAQ.query.get(faq_id)
        
        # Check if the FAQ exists
        if not faq:
            return jsonify({"error": "FAQ not found"}), 404

        # Delete the FAQ from the database
        db.session.delete(faq)
        db.session.commit()

        return jsonify({"message": f"FAQ with ID {faq_id} deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


