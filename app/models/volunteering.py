from datetime import datetime 
from app import db

class Volunteering(db.Model):
    volunteering_id = db.Column(db.Integer, primary_key=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)  # Application timestamp

    # Relationships
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), nullable=False)
    donor = db.relationship('Donor', backref=db.backref('volunteering_applications', lazy=True))

    def __repr__(self):
        return f'<Volunteering {self.volunteering_id} by Donor {self.donor_id}>'
