import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash
from app.models import Donor, StaffMember, Admin, Manager
from app import db
from app.models.blood_bank import BloodBank
from app.models.registration_request import RegistrationRequest
from app.services.email_service import send_email

manager_bp = Blueprint('manager', __name__)

def generate_numeric_password():
    return str(random.randint(100000, 999999))

@manager_bp.route('/request_registration', methods=['POST'])
def request_registration():
    data = request.get_json()

    manager_email = data.get('manager_email')
    existing_request = RegistrationRequest.query.filter_by(manager_email=manager_email).first()

    # Check if the email is already in use by any user type or existing request
    if (StaffMember.query.filter_by(email=manager_email).first() or
        Donor.query.filter_by(email=manager_email).first() or
        Admin.query.filter_by(email=manager_email).first() or
        Manager.query.filter_by(email=manager_email).first() or
        existing_request):
        return jsonify({"error": "Email already in use"}), 409

    # Create a new registration request
    new_request = RegistrationRequest(
        manager_name=data.get('manager_name'),
        manager_email=manager_email,
        manager_position=data.get('manager_position'),
        organization_name=data.get('organization_name'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        contact_info=data.get('contact_info'),
        start_hour=data.get('start_hour'),
        close_hour=data.get('close_hour')
    )

    db.session.add(new_request)
    db.session.commit()

    return jsonify({"message": "Registration request submitted successfully"}), 200


# Desktop 3
@manager_bp.route('/create-staff', methods=['POST'])
@jwt_required()  
def create_staff():
    current_user_id = get_jwt_identity()

    manager = Manager.query.get(current_user_id)

    if not manager:
        return jsonify({"error": "Unauthorized access."}), 403

    data = request.get_json()
    full_name = data.get('full_name')
    role = data.get('role')
    email = data.get('email')
    password = generate_numeric_password()

    if (StaffMember.query.filter_by(email=email).first() or
        Donor.query.filter_by(email=email).first() or
        Admin.query.filter_by(email=email).first() or
        Manager.query.filter_by(email=email).first()):

        return jsonify({"error": "Email already in use"}), 409

    # Get the next available Staff ID
    max_staff_id = StaffMember.query.filter(StaffMember.id.between(300000, 399999)).order_by(StaffMember.id.desc()).first()
    next_staff_id = (max_staff_id.id + 1) if max_staff_id else 300000  

    hashed_password = generate_password_hash(password)

    mb = ("Welcome to the Blood Line team! Your account has been successfully created,\n"
          "and you can now log in to manage blood donation activities.\n\n"
          f"Password : {password}")
    email_response = send_email("Welcome to the Blood Line Team!", [email], mb)
    if email_response:
        return jsonify(email_response), 500

    new_staff_member = StaffMember(
        id=next_staff_id,
        username=full_name,
        email=email,
        password=hashed_password,
        role=role,
        blood_bank_id=manager.blood_bank_id  
    )

    db.session.add(new_staff_member)
    db.session.commit()

    return jsonify({"message": f"Staff member created successfully, pass: {password}"}), 200


# Desktop 4
@manager_bp.route('/get-staff', methods=['GET'])
@jwt_required()
def get_staff():

    current_user_id = get_jwt_identity()
    manager = Manager.query.get(current_user_id)

    if not manager:
        return jsonify({"error": "Unauthorized access."}), 403

    staff_members = StaffMember.query.filter_by(blood_bank_id=manager.blood_bank_id).all()

    staff_list = [
        {
            "id": staff.id,
            "username": staff.username,
            "email": staff.email,
            "role": staff.role,
        }
        for staff in staff_members
    ]

    return jsonify({"staff": staff_list}), 200

# Desktop 5
@manager_bp.route('/delete-staff/<int:staff_id>', methods=['DELETE'])
@jwt_required()
def delete_staff_member(staff_id):
    current_user_id = get_jwt_identity()
    manager = Manager.query.get(current_user_id)

    if not manager:
        return jsonify({"error": "Unauthorized access."}), 403

    # Fetch the staff member by ID and check if they belong to the manager's blood bank
    staff_member = StaffMember.query.get(staff_id)
    if not staff_member or staff_member.blood_bank_id != manager.blood_bank_id:
        return jsonify({"error": "Staff member not found or unauthorized action"}), 403

    # Delete the staff member
    db.session.delete(staff_member)
    db.session.commit()

    return jsonify({"message": "Staff member deleted successfully"}), 200


@manager_bp.route('/desktop/contactus', methods=['GET', 'PUT'])
@jwt_required()
def manage_contact_us():
    # Get the ID of the current authenticated user
    current_user_id = get_jwt_identity()

    try:
        # Check if the current user is a manager
        manager = Manager.query.get(current_user_id)
        if not manager:
            return jsonify({"error": "Manager not found or not authorized"}), 403

        # Fetch the associated blood bank
        blood_bank = BloodBank.query.get(manager.blood_bank_id)
        if not blood_bank:
            return jsonify({"error": "Associated blood bank not found"}), 404

        if request.method == 'GET':
            # Retrieve and return the contact us details
            contact_us_details = {
                "blood_bank": blood_bank.name,
                "latitude": blood_bank.latitude,
                "longitude": blood_bank.longitude,
                "phone": blood_bank.phone_number,
                "email": blood_bank.email,
                "start_hour": blood_bank.start_hour,
                "close_hour": blood_bank.close_hour
            }
            return jsonify(contact_us_details), 200

        elif request.method == 'PUT':
            # Update contact us details
            data = request.get_json()

            # Update blood bank details
            blood_bank.name = data.get('blood_bank', blood_bank.name)
            blood_bank.latitude = data.get('latitude', blood_bank.latitude)
            blood_bank.longitude = data.get('longitude', blood_bank.longitude)
            blood_bank.phone_number = data.get('phone', blood_bank.phone_number)
            blood_bank.email = data.get('email', blood_bank.email)
            blood_bank.start_hour = data.get('start_hour', blood_bank.start_hour)
            blood_bank.close_hour = data.get('close_hour', blood_bank.close_hour)

            # Save changes to the database
            db.session.commit()

            return jsonify({"message": "Contact Us details updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


