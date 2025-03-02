from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import Donor, StaffMember, Admin, Manager
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db
from app.models.appointment import Appointment
from app.models.blood_bank import BloodBank
from app.models.blood_donation import BloodDonation
from app.models.blood_need import BloodNeed
from app.models.disease import Disease, DonorDisease
from app.models.event import Event
from app.models.faq import FAQ
from app.models.volunteering import Volunteering

donor_bp = Blueprint('donor', __name__)

def get_compatible_blood_types(blood_group):
    """Determine compatible blood types for donations (who can receive from the donor)."""
    compatibility = {
        "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
        "O+": ["O+", "A+", "B+", "AB+"],
        "A-": ["A-", "A+", "AB-", "AB+"],
        "A+": ["A+", "AB+"],
        "B-": ["B-", "B+", "AB-", "AB+"],
        "B+": ["B+", "AB+"],
        "AB-": ["AB-", "AB+"],
        "AB+": ["AB+"]
    }
    return compatibility.get(blood_group, [])

@donor_bp.route('/create_donor', methods=['POST'])
def create_donor():
    data = request.get_json()
    required_fields = ['username', 'email', 'password', 'weight', 'id_number', 'blood_group', 'barth']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    email = data['email']
    if (StaffMember.query.filter_by(email=email).first() or
        Donor.query.filter_by(email=email).first() or
        Admin.query.filter_by(email=email).first() or
        Manager.query.filter_by(email=email).first()):
        return jsonify({"error": "Email already in use"}), 409

    try:
        date_of_birth = datetime.strptime(data['barth'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date_of_birth format. Use YYYY-MM-DD.'}), 400

    max_donor_id = Donor.query.filter(Donor.id.between(10000, 199999)).order_by(Donor.id.desc()).first()
    next_donor_id = (max_donor_id.id + 1) if max_donor_id else 10000  

    new_donor = Donor(
        id=next_donor_id,
        username=data['username'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        gender=data.get('gender'),
        weight=data['weight'],
        id_number=data['id_number'],
        blood_group=data['blood_group'],
        date_of_birth=date_of_birth  
    )

    db.session.add(new_donor)
    db.session.commit()
    return jsonify({'message': 'Donor created successfully!'}), 201


@donor_bp.route('/blood_banks', methods=['GET'])
@jwt_required()
def get_blood_banks():
    blood_banks = BloodBank.query.all()

    blood_banks_data = [
        {
            'blood_bank_id': bank.blood_bank_id,
            'name': bank.name,
            'latitude': bank.latitude,  
            'longitude': bank.longitude,  
            'phone_number': bank.phone_number,
            'email': bank.email,
            'start_hour': bank.start_hour, 
            'close_hour': bank.close_hour, 
        }
        for bank in blood_banks
    ]

    return jsonify(blood_banks_data), 200

# Mobile 1
@donor_bp.route('/book_appointment', methods=['POST'])
@jwt_required()
def book_appointment():
    data = request.get_json()
    donor_id = get_jwt_identity()

    donor = Donor.query.get(donor_id)

    if not donor:
        return jsonify({"error": "Unauthorized access."}), 403
    
    blood_bank_id = data.get('blood_bank_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    donation_type = data.get('donation_type')
    diseases = data.get('diseases', [])

    if not all([blood_bank_id, appointment_date, appointment_time, donation_type]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Check if the donor already has a pending appointment
        existing_appointment = Appointment.query.filter_by(donor_id=donor_id, status="Pending").first()
        if existing_appointment:
            return jsonify({
                "error": "You already have a pending appointment",
                "appointment_id": existing_appointment.appointment_id,
                "appointment_date": existing_appointment.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": existing_appointment.appointment_time.strftime("%H:%M")
            }), 400

        # Create the appointment
        appointment = Appointment(
            donor_id=donor_id,
            blood_bank_id=blood_bank_id,
            appointment_date=datetime.strptime(appointment_date, "%Y-%m-%d"),
            appointment_time=datetime.strptime(appointment_time, "%H:%M").time(),
            status="Pending",
            donation_type=donation_type
        )
        db.session.add(appointment)
        db.session.flush()  # Get the appointment ID

        # Process diseases
        associated_diseases = []
        for disease_name in diseases:
            disease = Disease.query.filter_by(name=disease_name).first()
            if not disease:
                # Create the disease if it doesn't exist
                disease = Disease(name=disease_name)
                db.session.add(disease)
                db.session.flush()
            
            # Check if the donor-disease relationship already exists
            existing_donor_disease = DonorDisease.query.filter_by(donor_id=donor_id, disease_id=disease.disease_id).first()
            if not existing_donor_disease:
                # Link the disease to the donor only if it doesn't exist
                donor_disease = DonorDisease(donor_id=donor_id, disease_id=disease.disease_id)
                db.session.add(donor_disease)
                associated_diseases.append(disease.name)

        db.session.commit()


        return jsonify({
            "message": "Appointment booked successfully",
            "appointment_id": appointment.appointment_id,
            "associated_diseases": associated_diseases
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Mobile 2
@donor_bp.route('/check_pending_appointment', methods=['GET'])
@jwt_required()
def check_pending_appointment():
    try:
        # Get the donor ID from the JWT token
        donor_id = get_jwt_identity()

        donor = Donor.query.get(donor_id)

        if not donor:
            return jsonify({"error": "Unauthorized access."}), 403

        # Current date for comparison
        today = datetime.utcnow().date()

        # Delete expired appointments
        expired_appointments = Appointment.query.filter(
            Appointment.donor_id == donor_id,
            Appointment.appointment_date < today
        ).all()

        for appointment in expired_appointments:
            db.session.delete(appointment)
        db.session.commit()

        # Check for pending appointments
        pending_appointment = Appointment.query.filter_by(
            donor_id=donor_id,
            status='Pending'
        ).first()

        if pending_appointment:
            return jsonify({
                "appointment_id": pending_appointment.appointment_id,
                "blood_bank": pending_appointment.blood_bank.name,  # Access blood bank name through the relationship
                "appointment_date": pending_appointment.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": pending_appointment.appointment_time.strftime("%H:%M"),
                "donation_type": pending_appointment.donation_type,
                "status": pending_appointment.status
            }), 201
        else:
            return jsonify({"message": "No pending appointments found."}), 200

    except Exception as e:
        return jsonify({
            "message": "An error occurred while checking appointments.",
            "error": str(e)
        }), 500

# Mobile 3
@donor_bp.route('/delete_appointment', methods=['DELETE'])
@jwt_required()
def delete_appointment():
    try:
        donor_id = get_jwt_identity()

        donor = Donor.query.get(donor_id)

        if not donor:
            return jsonify({"error": "Unauthorized access."}), 403
        

        pending_appointment = Appointment.query.filter_by(
            donor_id=donor_id, 
            status='Pending'
        ).first()

        if not pending_appointment:
            return jsonify({"error": "No pending appointment found to delete"}), 404

        donor_diseases = DonorDisease.query.filter_by(donor_id=donor_id).all()
        for donor_disease in donor_diseases:
            db.session.delete(donor_disease)

        db.session.delete(pending_appointment)
        db.session.commit()

        return jsonify({"message": "Appointment deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while deleting the appointment: {str(e)}"}), 500
    

# Mobile 4
@donor_bp.route('/donor/follow_blood_bank', methods=['POST'])
@jwt_required()
def follow_blood_bank():
    # Get the current authenticated user's ID
    current_user_id = get_jwt_identity()

    donor = Donor.query.get(current_user_id)

    if not donor:
        return jsonify({"error": "Unauthorized access."}), 403
    
    data = request.get_json()
    blood_bank_id = data.get('blood_bank_id')
    
    # Validate input
    if not blood_bank_id:
        return jsonify({"error": "Blood bank ID is required"}), 400
    
    try:
        # Find the current donor and the blood bank
        donor = Donor.query.get(current_user_id)
        blood_bank = BloodBank.query.get(blood_bank_id)
        
        # Check if both donor and blood bank exist
        if not donor:
            return jsonify({"error": "Donor not found"}), 404
        
        if not blood_bank:
            return jsonify({"error": "Blood bank not found"}), 404
        
        # Check if already following
        if donor.followed_blood_banks.filter_by(blood_bank_id=blood_bank_id).first():
            return jsonify({"message": "Already following this blood bank"}), 400
        
        # Add blood bank to followed banks
        donor.followed_blood_banks.append(blood_bank)
        db.session.commit()
        
        return jsonify({
            "message": "Blood bank followed successfully",
            "blood_bank": {
                "id": blood_bank.blood_bank_id,
                "name": blood_bank.name
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# Mobile 5
@donor_bp.route('/donor/unfollow_blood_bank', methods=['POST'])
@jwt_required()
def unfollow_blood_bank():
    # Get the current authenticated user's ID
    current_user_id = get_jwt_identity()

    donor = Donor.query.get(current_user_id)

    if not donor:
        return jsonify({"error": "Unauthorized access."}), 403
    
    data = request.get_json()
    blood_bank_id = data.get('blood_bank_id')
    
    # Validate input
    if not blood_bank_id:
        return jsonify({"error": "Blood bank ID is required"}), 400
    
    try:
        # Find the current donor and the blood bank
        donor = Donor.query.get(current_user_id)
        blood_bank = BloodBank.query.get(blood_bank_id)
        
        # Check if both donor and blood bank exist
        if not donor:
            return jsonify({"error": "Donor not found"}), 404
        
        if not blood_bank:
            return jsonify({"error": "Blood bank not found"}), 404
        
        # Check if donor is not following the blood bank
        if not donor.followed_blood_banks.filter_by(blood_bank_id=blood_bank_id).first():
            return jsonify({"message": "Not following this blood bank"}), 400
        
        # Remove blood bank from followed banks
        donor.followed_blood_banks.remove(blood_bank)
        db.session.commit()
        
        return jsonify({
            "message": "Blood bank unfollowed successfully",
            "blood_bank": {
                "id": blood_bank.blood_bank_id,
                "name": blood_bank.name
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# Mobile 6
@donor_bp.route('/donor/followed_blood_banks', methods=['GET'])
@jwt_required()
def get_followed_blood_banks():
    # Get the current authenticated user's ID
    current_user_id = get_jwt_identity()
    
    try:
        # Find the current donor
        donor = Donor.query.get(current_user_id)

        if not donor:
            return jsonify({"error": "Unauthorized access."}), 403
        
        # Retrieve followed blood banks
        followed_banks = [{
            "id": bank.blood_bank_id,
            "name": bank.name,
            "latitude": bank.latitude,
            "longitude": bank.longitude,
            "phone_number": bank.phone_number,
            "email": bank.email,
            "start_hour": bank.start_hour,
            "close_hour": bank.close_hour
        } for bank in donor.followed_blood_banks.all()]
        
        return jsonify({
            "followed_blood_banks": followed_banks,
        }), 200
    
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@donor_bp.route('/donor/faqs', methods=['GET'])
@jwt_required()
def get_faqs():
    try:
        faqs = FAQ.query.all()
        faq_list = [{
            "id": faq.faq_id,
            "question": faq.question,
            "answer": faq.answer
        } for faq in faqs]

        return jsonify({
            "faqs": faq_list,
            "count": len(faq_list)
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@donor_bp.route('/toggle_volunteering', methods=['POST'])
@jwt_required()
def toggle_volunteering():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can toggle volunteering status."}), 403

        # Check if the donor is already a volunteer
        existing_volunteering = Volunteering.query.filter_by(donor_id=donor.id).first()

        if existing_volunteering:
            # Remove the donor from the volunteering program
            db.session.delete(existing_volunteering)
            db.session.commit()
            return jsonify({
                "message": "You have successfully withdrawn from the volunteering program."
            }), 200
        else:
            # Add the donor to the volunteering program
            new_volunteering = Volunteering(donor_id=donor.id, applied_at=datetime.utcnow())
            db.session.add(new_volunteering)
            db.session.commit()
            return jsonify({
                "message": "You have successfully joined the volunteering program."
            }), 201

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500
    

@donor_bp.route('/donation_history', methods=['GET'])
@jwt_required()
def donation_history():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can view donation history."}), 403

        # Fetch the donor's donation history
        donations = (
            BloodDonation.query
            .filter_by(donor_id=donor.id)
            .order_by(BloodDonation.donation_date.desc())
            .all()
        )

        if not donations:
            return jsonify({
                "message": "No donation history found.",
                "next_eligible_donation_date": None,
                "donation_history": []
            }), 200

        # Format donation history
        donation_history = []
        for donation in donations:
            donation_history.append({
                "donation_id": donation.donation_id,
                "blood_bank_name": donation.blood_bank.name,
                "donation_date": donation.donation_date.strftime("%Y-%m-%d"),
                "donation_type": donation.donation_type,
                "quantity_donated": donation.quantity_donated,
                "donor_blood_pulse": donation.donor_blood_pulse,
                "donor_temperature": donation.donor_temperature,
                "blood_pressure": donation.blood_pressure,
            })

        # Determine the next eligible donation date
        last_donation_date = donations[0].donation_date
        next_eligible_donation_date = last_donation_date + timedelta(days=56)  # 56 days is a common interval

        return jsonify({
            "message": "Donation history retrieved successfully.",
            "next_eligible_donation_date": next_eligible_donation_date.strftime("%Y-%m-%d"),
            "donation_history": donation_history
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500


@donor_bp.route('/blood_bank_events', methods=['GET'])
@jwt_required()
def get_blood_bank_events():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can retrieve blood bank events."}), 403

        # Get current date to filter past events
        today = datetime.utcnow().date()

        # Query events from blood banks the donor follows
        followed_blood_banks = donor.followed_blood_banks.all()  # Get all followed blood banks
        events = (
            Event.query.join(BloodBank)
            .filter(
                Event.blood_bank_id.in_([bank.blood_bank_id for bank in followed_blood_banks]),
                Event.event_date >= today  # Only include upcoming events
            )
            .order_by(Event.event_date, Event.event_time)  # Order by date and time
            .all()
        )

        # Prepare the events response
        events_data = [
            {
                "event_id": event.event_id,
                "title": event.title,
                "description": event.description,
                "event_date": event.event_date.strftime('%Y-%m-%d'),
                "event_time": event.event_time.strftime('%H:%M'),
                "location": event.location,
                "blood_bank_id": event.blood_bank_id,
                "blood_bank_name": BloodBank.query.get(event.blood_bank_id).name  # Get the name of the blood bank
            }
            for event in events
        ]

        return jsonify({
            "events": events_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500
    

@donor_bp.route('/blood_bank_needs', methods=['GET'])
@jwt_required()
def get_blood_bank_needs():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the donor's information
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can retrieve blood needs."}), 403

        # Determine compatible blood types
        compatible_blood_types = get_compatible_blood_types(donor.blood_group)

        # Get current date and time
        now = datetime.utcnow()

        # Fetch blood needs from followed blood banks
        followed_blood_banks = donor.followed_blood_banks.all()
        blood_needs = (
            BloodNeed.query
            .filter(
                BloodNeed.blood_bank_id.in_([bank.blood_bank_id for bank in followed_blood_banks]),
                BloodNeed.blood_types.in_(get_compatible_blood_types(donor.blood_group)),
                (BloodNeed.expire_date > now.date()) | ((BloodNeed.expire_date == now.date()) & (BloodNeed.expire_time > now.time()))
            )
            .order_by(BloodNeed.expire_date, BloodNeed.expire_time)
            .all()
        )


        # Remove expired blood needs
        expired_blood_needs = BloodNeed.query.filter(
            (BloodNeed.expire_date < now.date()) | ((BloodNeed.expire_date == now.date()) & (BloodNeed.expire_time <= now.time()))
        ).all()
        for expired in expired_blood_needs:
            db.session.delete(expired)
        db.session.commit()

        # Prepare the blood needs response
        blood_needs_data = [
            {
                "blood_need_id": need.blood_need_id,
                "blood_type": need.blood_types,
                "units": need.units,
                "location": need.location,
                "hospital": need.hospital,
                "expire_date": need.expire_date.strftime('%Y-%m-%d'),
                "expire_time": need.expire_time.strftime('%H:%M'),
                "blood_bank_id": need.blood_bank_id,
                "blood_bank_name": BloodBank.query.get(need.blood_bank_id).name
            }
            for need in blood_needs
        ]

        return jsonify({
            "blood_needs": blood_needs_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500


@donor_bp.route('/update_donor_profile', methods=['PUT'])
@jwt_required()
def update_donor_profile():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can update their profile."}), 403

        # Parse the request data
        data = request.get_json()

        # Update the donor's profile
        if 'username' in data:
            donor.username = data['username']
        if 'email' in data:
            email = data['email']
            if (StaffMember.query.filter_by(email=email).first() or
            Donor.query.filter_by(email=email).first() or
            Admin.query.filter_by(email=email).first() or
            Manager.query.filter_by(email=email).first()):
                return jsonify({"error": "Email already in use"}), 409
            donor.email = data['email']
        if 'phone_number' in data:
            donor.phone_number = data['phone_number']
        if 'blood_group' in data:
            donor.blood_group = data['blood_group']

        # Commit changes to the database
        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully.",
            "updated_data": {
                "username": donor.username,
                "email": donor.email,
                "phone_number": donor.phone_number,
                "blood_group": donor.blood_group
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500


@donor_bp.route('/get_donor_name', methods=['GET'])
@jwt_required()
def get_donor_name():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can access their name."}), 403

        # Return the donor's name
        return jsonify({"donor_name": donor.username}), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500
    