from app import db

class BloodDonation(db.Model):
    donation_id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), nullable=False)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.appointment_id'), nullable=True)
    donation_date = db.Column(db.Date, nullable=False)
    donation_type = db.Column(db.String(100), nullable=False)
    quantity_donated = db.Column(db.Float, nullable=False) # Unit
    recipient_organization = db.Column(db.String(200), nullable=True)
    donor_blood_pulse = db.Column(db.Float, nullable=False) 
    donor_temperature = db.Column(db.Float, nullable=False)  
    blood_pressure = db.Column(db.String(50), nullable=False) 

    def __repr__(self):
        return f'<BloodDonation {self.donation_id}>'