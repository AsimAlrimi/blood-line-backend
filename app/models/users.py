from app import db

class User(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    profile_image = db.Column(db.String(200), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Donor(User):
    weight = db.Column(db.Float, nullable=False)
    id_number = db.Column(db.String(200), nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    ranking_points = db.Column(db.Integer, default=0)

    # Relationships
    appointments = db.relationship('Appointment', backref='donor', lazy=True)
    donations = db.relationship('BloodDonation', backref='donor', lazy=True)
    diseases = db.relationship('Disease', secondary='donor_disease', backref='donors', lazy='dynamic')
    followed_blood_banks = db.relationship('BloodBank', secondary='donor_blood_bank', back_populates='followers', lazy='dynamic')

    def __repr__(self):
        return f'<Donor {self.username}>'


class Admin(User):
    # Additional fields specific to Admin can be added here
    faqs = db.relationship('FAQ', backref='admin', lazy=True)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Manager(User):
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)

    def __repr__(self):
        return f'<Manager {self.username}>'


class StaffMember(User):
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)
    role = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<StaffMember {self.username}>'