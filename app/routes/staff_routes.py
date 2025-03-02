from datetime import date, timedelta, datetime 
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import Donor, StaffMember, Admin, Manager
from app import db
from app.models.appointment import Appointment
from app.models.blood_bank import BloodBank
from app.models.blood_need import BloodNeed
from app.models.event import Event
from app.models.blood_donation import BloodDonation
from app.models.blood_inventory import BloodInventory
from app.models.volunteering import Volunteering

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/blood_inventory', methods=['GET'])
@jwt_required()
def get_blood_inventory():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()
        
        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()
        
        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Fetch the blood inventory for the associated blood bank
        inventory = BloodInventory.query.filter_by(blood_bank_ID=blood_bank_id).all()
        
        # Convert the inventory data into a list of dictionaries
        inventory_list = [{
            "inventory_id": item.Inventory_ID,
            "blood_type": item.Blood_Type,
            "quantity": item.Quantity,
            "expiration_date": item.Expiration_Date.strftime('%Y-%m-%d')
        } for item in inventory]

        return jsonify({
            "inventory": inventory_list,
            "count": len(inventory_list)
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/blood_inventory/take', methods=['POST'])
@jwt_required()
def take_blood_unit():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()
        
        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()
        
        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Parse the request data
        data = request.get_json()
        blood_type = data.get('blood_type')
        quantity = data.get('quantity')

        if not blood_type or not quantity:
            return jsonify({"error": "Missing 'blood_type' or 'quantity' in request"}), 400

        if quantity <= 0:
            return jsonify({"error": "Quantity must be a positive number"}), 400

        # Fetch the inventory record for the requested blood type
        inventory_item = BloodInventory.query.filter_by(
            blood_bank_ID=blood_bank_id, Blood_Type=blood_type
        ).first()

        if not inventory_item:
            return jsonify({"error": f"No inventory found for blood type {blood_type}"}), 404

        # Check if there are enough units available
        if inventory_item.Quantity < quantity:
            return jsonify({
                "error": f"Insufficient units of {blood_type} available",
                "available_quantity": inventory_item.Quantity
            }), 400

        # Deduct the requested quantity from the inventory
        inventory_item.Quantity -= quantity
        db.session.commit()

        return jsonify({
            "message": f"Successfully taken {quantity} units of {blood_type}",
            "remaining_quantity": inventory_item.Quantity
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/staff/today_appointments', methods=['Post'])
@jwt_required()
def get_today_appointments():
    # Get the current authenticated staff member's ID
    current_user_id = get_jwt_identity()
    data = request.get_json()
    status_type = data["page"]
    
    try:
        # Find the current staff member
        staff_member = StaffMember.query.get(current_user_id)

        if not staff_member:
            return jsonify({"error": "Staff member not found"}), 404

        # Check if the staff member is associated with a blood bank
        if not staff_member.blood_bank_id:
            return jsonify({"error": "Staff member is not associated with any blood bank"}), 400

        # Get today's date
        today = date.today()

        if status_type == "Appointmen":
            # Retrieve appointments for the blood bank that are scheduled for today and are pending
            appointments = Appointment.query.filter_by(
                blood_bank_id=staff_member.blood_bank_id,
                appointment_date=today, 
                status="Pending"
            ).all()

            # Format the data for response
            appointments_data = [{
                "id" : appointment.appointment_id,
                "Name": appointment.donor.username,  # Assuming Donor has a username field
                "Email": appointment.donor.email,   # Assuming Donor has an email field
                "Date": appointment.appointment_date.strftime('%Y-%m-%d'),
                "status" : appointment.status,
                "time": appointment.appointment_time.strftime('%H:%M:%S')  # Format the time
            } for appointment in appointments]

            return jsonify({
                "today_appointments": appointments_data,
            }), 200

        elif status_type == "Donation":
            # Retrieve appointments for the blood bank that are scheduled for today and are Open
            appointments = Appointment.query.filter_by(
                blood_bank_id=staff_member.blood_bank_id,
                appointment_date=today, 
                status="Open"
            ).all()

            # Format the data for response
            appointments_data = [{
                "id" : appointment.appointment_id,
                "Name": appointment.donor.username,  # Assuming Donor has a username field
                "Email": appointment.donor.email,   # Assuming Donor has an email field
                "Date": appointment.appointment_date.strftime('%Y-%m-%d'),
                "status" : appointment.status,
                "time": appointment.appointment_time.strftime('%H:%M:%S')  # Format the time
            } for appointment in appointments]

            return jsonify({
                "today_appointments": appointments_data,
            }), 200
        else:
            return jsonify({"error": "Wrong status input"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    
    
@staff_bp.route('/staff/open_appointment', methods=['POST'])
@jwt_required()
def open_appointment():
    # Get the current authenticated staff member's ID
    current_user_id = get_jwt_identity()
    

    try:
        # Get appointment ID from request data
        data = request.get_json()
        appointment_id = data.get('appointment_id')
        s = data['state']
        if not appointment_id:
            return jsonify({"error": "Appointment ID is required"}), 400

        # Find the current staff member
        staff_member = StaffMember.query.get(current_user_id)

        if not staff_member:
            return jsonify({"error": "Staff member not found"}), 404

        # Check if the staff member is associated with a blood bank
        if not staff_member.blood_bank_id:
            return jsonify({"error": "Staff member is not associated with any blood bank"}), 400

        # Retrieve the appointment
        appointment = Appointment.query.filter_by(
            appointment_id=appointment_id,
            blood_bank_id=staff_member.blood_bank_id
        ).first()

        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        if s == "cancel":
            # Check the current status of the appointment
            if appointment.status not in ['Open']:
                return jsonify({"error": "Appointment cannot be Canceled. Current status: {}".format(appointment.status)}), 400

            # Update the appointment status to 'Canceled'
            appointment.status = 'Canceled'
            db.session.commit()
            return jsonify({"message": "Appointment Canceled successfully"}), 200

        elif s == "open":
            # Check the current status of the appointment
            if appointment.status not in ['Pending']:
                return jsonify({"error": "Appointment cannot be opened. Current status: {}".format(appointment.status)}), 400

            # Update the appointment status to 'Open'
            appointment.status = 'Open'
            db.session.commit()

            return jsonify({"message": "Appointment opened successfully"}), 200
        else:
            return jsonify({"error": "Wrong status input"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    

@staff_bp.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
@jwt_required()
def complete_appointment(appointment_id):
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()

        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Fetch the appointment details
        appointment = Appointment.query.filter_by(appointment_id=appointment_id, status="Open").first()

        if not appointment:
            return jsonify({"error": "Appointment not found or already completed"}), 404

        # Validate staff input (blood type, quantity, pulse, temperature, etc.)
        data = request.json
        blood_type = data.get('blood_type')
        quantity_donated = data.get('quantity_donated')
        donor_blood_pulse = data.get('donor_blood_pulse')
        donor_temperature = data.get('donor_temperature')
        blood_pressure = data.get('blood_pressure')

        if not all([blood_type, quantity_donated, donor_blood_pulse, donor_temperature, blood_pressure]):
            return jsonify({"error": "Incomplete data provided"}), 400
        
        # Fetch the donor details
        donor = Donor.query.filter_by(id=appointment.donor_id).first()

        if not donor:
            return jsonify({"error": "Donor not found"}), 404

        # Check if the blood type matches the donor's record
        if donor.blood_group != blood_type:
            # Update the donor's blood group
            donor.blood_group = blood_type
            db.session.add(donor)

        # Record the donation
        donation = BloodDonation(
            donor_id=appointment.donor_id,
            blood_bank_id=staff_member.blood_bank_id,
            appointment_id=appointment_id,
            donation_date=date.today(),  # Ensure `datetime` is imported
            donation_type=appointment.donation_type,
            quantity_donated=quantity_donated,
            donor_blood_pulse=donor_blood_pulse,
            donor_temperature=donor_temperature,
            blood_pressure=blood_pressure
        )
        db.session.add(donation)

        # Update the blood inventory
        inventory = BloodInventory.query.filter_by(
            blood_bank_ID=staff_member.blood_bank_id, Blood_Type=blood_type
        ).first()

        if inventory:
            inventory.Quantity += quantity_donated
        else:
            # If the blood type does not exist in the inventory, create a new record
            expiration_date = date.today() + timedelta(days=42)
            new_inventory = BloodInventory(
                blood_bank_ID=staff_member.blood_bank_id,
                Blood_Type=blood_type,
                Quantity=quantity_donated,
                Expiration_Date=expiration_date
            )
            db.session.add(new_inventory)

        # Mark the appointment as completed
        appointment.status = "Complete"
        db.session.commit()

        return jsonify({"message": "Appointment completed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/donors', methods=['GET'])
@jwt_required()
def get_donors():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()

        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Fetch the donations for the associated blood bank
        donations = BloodDonation.query.filter_by(blood_bank_id=blood_bank_id).all()

        if not donations:
            return jsonify({
                "message": "No donations found for this blood bank.",
                "donors": []
            }), 200

        # Fetch unique donors for the donations
        donor_ids = {donation.donor_id for donation in donations}
        donors = Donor.query.filter(Donor.id.in_(donor_ids)).all()

        # Convert donor data into a list of dictionaries
        donor_list = [{
            "name": donor.username,
            "blood_type": donor.blood_group,
            "email": donor.email,
            "age": (date.today().year - donor.date_of_birth.year) if donor.date_of_birth else None,
            "gender": donor.gender,
        } for donor in donors]

        return jsonify({
            "donors": donor_list,
            "count": len(donor_list)
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/volunteering_status', methods=['GET'])
@jwt_required()
def get_volunteering_status():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Check if the current user is a donor
        donor = Donor.query.filter_by(id=current_user_id).first()
        if not donor:
            return jsonify({"error": "Unauthorized access. Only donors can check volunteering status."}), 403

        # Check if the donor is a volunteer
        existing_volunteering = Volunteering.query.filter_by(donor_id=donor.id).first()

        return jsonify({
            "is_volunteer": existing_volunteering is not None
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500


@staff_bp.route('/volunteers', methods=['GET'])
@jwt_required()
def get_volunteers():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Verify if the current user is a staff member
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()
        if not staff_member:
            return jsonify({"error": "Unauthorized access. Only staff members can view volunteers."}), 403

        # Query all volunteers from the database
        volunteers = Volunteering.query.join(Donor, Volunteering.donor_id == Donor.id).all()

        # Prepare a list of volunteer information
        volunteers_list = [{
            "name": donor.username,
            "email": donor.email,
            "phone_number": donor.phone_number,
            "gender": donor.gender
        } for volunteer in volunteers for donor in [volunteer.donor]]

        return jsonify({
            "volunteers": volunteers_list,
            "count": len(volunteers_list)
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500
    

@staff_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()

        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Get the event data from the request body
        data = request.json
        title = data.get('title')
        description = data.get('description')
        event_date = data.get('event_date')
        event_time = data.get('event_time')
        location = data.get('location')

        # Validate required fields
        if not all([title, description, event_date, event_time, location]):
            return jsonify({"error": "All fields are required"}), 400

        # Convert event_date and event_time to appropriate types
        try:
            event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
            event_time = datetime.strptime(event_time, '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Invalid date or time format"}), 400

        # Create a new Event instance
        new_event = Event(
            title=title,
            description=description,
            event_date=event_date,
            event_time=event_time,
            location=location,
            blood_bank_id=blood_bank_id
        )

        # Add the new event to the database
        db.session.add(new_event)
        db.session.commit()

        return jsonify({"message": "Event created successfully", "event_id": new_event.event_id}), 201

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/get/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()

        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Fetch all events for the associated blood bank
        events = Event.query.filter_by(blood_bank_id=blood_bank_id).all()

        # Get the current date
        current_date = datetime.now().date()

        # Filter and delete past events
        for event in events:
            if event.event_date < current_date:
                db.session.delete(event)

        # Commit the deletions
        db.session.commit()

        # Re-fetch the events after deletion
        events = Event.query.filter_by(blood_bank_id=blood_bank_id).all()

        # Convert event data into a list of dictionaries
        event_list = [{
            "event_id": event.event_id,
            "title": event.title,
            "description": event.description,
            "event_date": event.event_date.strftime('%Y-%m-%d'),
            "event_time": event.event_time.strftime('%H:%M:%S'),
            "location": event.location
        } for event in events]

        return jsonify({
            "events": event_list,
            "count": len(event_list)
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/delete/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    try:
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()

        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank ID associated with the staff member
        blood_bank_id = staff_member.blood_bank_id

        # Fetch the event to be deleted
        event = Event.query.filter_by(event_id=event_id, blood_bank_id=blood_bank_id).first()

        if not event:
            return jsonify({"error": "Event not found or not authorized to delete"}), 404

        # Delete the event
        db.session.delete(event)
        db.session.commit()

        return jsonify({"message": "Event deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@staff_bp.route('/blood_need', methods=['POST'])
@jwt_required()
def create_blood_need():
    try:
        data = request.get_json()
        
        # Get the current user ID from the JWT
        current_user_id = get_jwt_identity()

        # Fetch the staff member's details
        staff_member = StaffMember.query.filter_by(id=current_user_id).first()
        if not staff_member:
            return jsonify({"error": "Unauthorized access"}), 403

        # Get the blood bank associated with the staff member
        blood_bank = BloodBank.query.filter_by(blood_bank_id=staff_member.blood_bank_id).first()
        if not blood_bank:
            return jsonify({"error": "Blood bank not found"}), 404

        # Get required fields from request data
        blood_types = data.get('bloodTypes')
        units = data.get('units')
        location = data.get('location')
        expire_date_str = data.get('expireDate')
        expire_time_str = data.get('expireTime')

        # Validate inputs
        if not all([blood_types, units, location, expire_date_str, expire_time_str]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Convert string inputs to date and time objects
        expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').date()
        expire_time = datetime.strptime(expire_time_str, '%H:%M').time()

        # Create a new BloodNeed
        new_blood_need = BloodNeed(
            blood_types=blood_types,
            units=units,
            location=location,
            hospital=blood_bank.name,  # Use the blood bank name as the hospital
            expire_date=expire_date,
            expire_time=expire_time,
            blood_bank_id=blood_bank.blood_bank_id
        )

        # Save to database
        db.session.add(new_blood_need)
        db.session.commit()

        return jsonify({'message': 'Blood need created successfully', 'bloodNeed': new_blood_need.blood_types}), 201

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

