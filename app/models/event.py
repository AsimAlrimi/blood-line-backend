from app import db

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)  # Foreign key linking to BloodBank

    def __repr__(self):
        return f'<Event {self.title}>'
