from app import db

class BloodBank(db.Model):
    blood_bank_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    phone_number = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    start_hour = db.Column(db.String(10), nullable=False)
    close_hour = db.Column(db.String(10), nullable=False)

    # Relationships
    appointments = db.relationship('Appointment', backref='blood_bank', lazy=True)
    donations = db.relationship('BloodDonation', backref='blood_bank', lazy=True)
    inventories = db.relationship('BloodInventory', backref='blood_bank', lazy=True)
    events = db.relationship('Event', backref='blood_bank', lazy=True)
    staff_members = db.relationship('StaffMember', backref='blood_bank', lazy=True)
    followers = db.relationship('Donor', secondary='donor_blood_bank', back_populates='followed_blood_banks', lazy='dynamic')

    def __repr__(self):
        return f'<BloodBank {self.name}>'
    
class DonorBloodBank(db.Model):
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), primary_key=True)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), primary_key=True)