from datetime import datetime, timedelta
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash
from app import jwt
from app.models import Donor, StaffMember, Admin, Manager
from werkzeug.security import check_password_hash
from app import db
from app.models.blacklist import Blacklist
from app.models.blood_bank import BloodBank
from app.models.blood_donation import BloodDonation
from app.models.blood_need import BloodNeed
from app.models.email_verification import EmailVerification
from app.models.event import Event
from app.services.email_service import send_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    # Query the user by email (check all user types)
    user = Donor.query.filter_by(email=email).first() or \
           Admin.query.filter_by(email=email).first() or \
           Manager.query.filter_by(email=email).first() or \
           StaffMember.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Wrong email or password"}), 401

    access_token = create_access_token(identity=str(user.id))

    # Determine the user type
    user_type = None
    if isinstance(user, Admin):
        user_type = 'Admin'
    elif isinstance(user, Manager):
        user_type = 'Manager'
    elif isinstance(user, StaffMember):
        user_type = 'StaffMember'
    else:
        user_type = 'Donor'

    user_name = user.username if hasattr(user, 'username') else 'User'

    return jsonify(
        access_token=access_token,
        user_type=user_type,
        user_name=user_name
    ), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']

    if Blacklist.query.filter_by(jti=jti).first():
        return jsonify({"msg": "Token already blacklisted"}), 400

    blacklisted_token = Blacklist(jti=jti)
    db.session.add(blacklisted_token)
    db.session.commit()

    return jsonify({"msg": "Successfully logged out"}), 200


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']

    return Blacklist.query.filter_by(jti=jti).first() is not None


@auth_bp.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    email = data.get("email")
    newAccount = data.get("newAccount")
    
    if not email:
        return jsonify({"msg": "Email is required"}), 400
    
    user = (StaffMember.query.filter_by(email=email).first() or
    Donor.query.filter_by(email=email).first() or
    Admin.query.filter_by(email=email).first() or
    Manager.query.filter_by(email=email).first())

    if newAccount and user:
        return jsonify({"error": "Email already in use"}), 409
    elif (not newAccount and not user):
        return jsonify({"error": "User not found"}), 404 

    try:
        # Generate a 5-digit code
        verification_code = random.randint(10000, 99999)

        # Save code in DB or cache
        verification = EmailVerification(email=email, code=verification_code)
        db.session.add(verification)
        db.session.commit()

        # Send the code via email
        subject = "Your Verification Code"
        body = f"Your verification code is: {verification_code}"
        send_email(subject, [email], body)

        return jsonify({"msg": "Verification code sent successfully"}), 200

    except Exception as e:
        return jsonify({"msg": "Failed to send code", "error": str(e)}), 500
    

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        return jsonify({"msg": "Email and code are required"}), 400

    verification = EmailVerification.query.filter_by(email=email, code=code).first()

    if verification:
        # Code is correct, proceed
        db.session.delete(verification)  # Optionally delete the code
        db.session.commit()
        return jsonify({"msg": "Verification successful"}), 200

    return jsonify({"msg": "Invalid or expired code"}), 400


@auth_bp.route('/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    email = data.get("email")
    new_password = data.get("newPassword")

    if not email or not new_password:
        return jsonify({"msg": "Email and new password are required"}), 400

    user = (StaffMember.query.filter_by(email=email).first() or
            Donor.query.filter_by(email=email).first() or
            Admin.query.filter_by(email=email).first() or
            Manager.query.filter_by(email=email).first())

    if user:
        try:
            # Hash the new password
            hashed_password = generate_password_hash(new_password)
            user.password = hashed_password
            db.session.commit()
            return jsonify({"msg": "Password updated successfully"}), 200
        except Exception as e:
            return jsonify({"msg": "Failed to update password", "error": str(e)}), 500

    return jsonify({"msg": "User not found"}), 404


@auth_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id = get_jwt_identity()

    try:
        user = Donor.query.get(current_user_id) or \
               Admin.query.get(current_user_id) or \
               Manager.query.get(current_user_id) or \
               StaffMember.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Base user profile data
        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "gender": user.gender,
            "profile_image": user.profile_image,
            "date_of_birth": user.date_of_birth.strftime("%Y-%m-%d") if user.date_of_birth else None,
            "user_type": user.__class__.__name__
        }

        # Extend profile data based on user type
        if isinstance(user, Donor):
            profile_data.update({
                "weight": user.weight,
                "id_number": user.id_number,
                "blood_group": user.blood_group,
                "ranking_points": user.ranking_points
            })

        elif isinstance(user, Manager):
            profile_data.update({
                "blood_bank_id": user.blood_bank_id
            })

        elif isinstance(user, StaffMember):
            profile_data.update({
                "blood_bank_id": user.blood_bank_id,
                "role": user.role
            })
        return jsonify({"profile": profile_data}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    


@auth_bp.route('/desktop/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    current_user_id = get_jwt_identity()

    try:
        user = Donor.query.get(current_user_id) or \
               Admin.query.get(current_user_id) or \
               Manager.query.get(current_user_id) or \
               StaffMember.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        if 'email' in data:
            email = data['email']
            if (StaffMember.query.filter_by(email=email).first() or
            Donor.query.filter_by(email=email).first() or
            Admin.query.filter_by(email=email).first() or
            Manager.query.filter_by(email=email).first()):
                return jsonify({"error": "Email already in use"}), 409

        # Update user details
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.gender = data.get('gender', user.gender)

        # Save changes to the database
        db.session.commit()

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@auth_bp.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        user = (
            Donor.query.filter_by(id=current_user_id).first() or
            Admin.query.filter_by(id=current_user_id).first() or
            Manager.query.filter_by(id=current_user_id).first() or
            StaffMember.query.filter_by(id=current_user_id).first()
        )

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Parse the request body to get the old and new passwords
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        # Check if the old password is correct
        if not check_password_hash(user.password, old_password):
            return jsonify({"error": "Old password is incorrect"}), 400

        # Update the password with the new one
        user.password = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@auth_bp.route('/get_user_data', methods=['GET'])
@jwt_required()
def get_user_data():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check user role in a prioritized order
        user = Donor.query.get(current_user_id) or \
               Admin.query.get(current_user_id) or \
               Manager.query.get(current_user_id) or \
               StaffMember.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get the last 30 days range
        last_30_days = datetime.utcnow() - timedelta(days=30)

        if isinstance(user, Donor):
            # Donor: Return their name
            return jsonify({"error": "Unauthorized access"}), 403

        elif isinstance(user, Manager) or isinstance(user, StaffMember):
            # Manager/StaffMember: Return blood bank data for the past 30 days
            blood_bank_id = user.blood_bank_id
            blood_bank = BloodBank.query.get(blood_bank_id)
            if not blood_bank:
                return jsonify({"error": "Blood bank not found"}), 404

            donations_count = BloodDonation.query.filter(
                BloodDonation.blood_bank_id == blood_bank_id,
                BloodDonation.donation_date >= last_30_days
            ).count()

            events_count = Event.query.filter(
                Event.blood_bank_id == blood_bank_id,
                Event.event_date >= last_30_days
            ).count()

            blood_needs_count = BloodNeed.query.filter(
                BloodNeed.blood_bank_id == blood_bank_id,
                BloodNeed.created_at >= last_30_days
            ).count()

            return jsonify({
                "donations_count": donations_count,
                "events_count": events_count,
                "blood_needs_count": blood_needs_count
            }), 200

        elif isinstance(user, Admin):
            # Admin: Return data for all blood banks in the past 30 days
            donations_count = BloodDonation.query.filter(
                BloodDonation.donation_date >= last_30_days
            ).count()

            events_count = Event.query.filter(
                Event.event_date >= last_30_days
            ).count()

            blood_needs_count = BloodNeed.query.filter(
                BloodNeed.created_at >= last_30_days
            ).count()

            return jsonify({
                "donations_count": donations_count,
                "events_count": events_count,
                "blood_needs_count": blood_needs_count
            }), 200

        return jsonify({"error": "Unauthorized access."}), 403

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

