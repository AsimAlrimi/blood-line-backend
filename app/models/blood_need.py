from datetime import datetime 
from app import db

class BloodNeed(db.Model):
    blood_need_id = db.Column(db.Integer, primary_key=True)
    blood_types = db.Column(db.String(5), nullable=False)  # e.g., "AB+"
    units = db.Column(db.Float, nullable=False)  # e.g., 0.5 units
    location = db.Column(db.String(200), nullable=False)  # e.g., "Amman, ..."
    hospital = db.Column(db.String(200), nullable=False)  # e.g., "Hayat"
    expire_date = db.Column(db.Date, nullable=False)
    expire_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key and relationship
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)
    blood_bank = db.relationship('BloodBank', backref=db.backref('blood_needs', lazy=True))

    def __repr__(self):
        return f'<BloodNeed {self.blood_types} at {self.hospital}>' 