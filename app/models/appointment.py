from app import db

class Appointment(db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), nullable=False)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(100), nullable=False)  # Pending, Open, Complete, Canceled
    donation_type = db.Column(db.String(100), nullable=False)
    quantity_donated = db.Column(db.Float, nullable=True)  # Optional, if donation occurs
    previous_donations = db.Column(db.Integer, nullable=True)

    donations = db.relationship('BloodDonation', backref='appointment', lazy=True)

    def __repr__(self):
        return f'<Appointment {self.appointment_id}>'