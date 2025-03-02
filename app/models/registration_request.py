from app import db

class RegistrationRequest(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    manager_name = db.Column(db.String(100), nullable=False)
    manager_email = db.Column(db.String(100), nullable=False)
    manager_position = db.Column(db.String(100), nullable=False)
    organization_name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)  # Replacing organization_address
    longitude = db.Column(db.Float, nullable=False)  # Replacing organization_address
    contact_info = db.Column(db.String(200), nullable=False)
    start_hour = db.Column(db.String(10), nullable=False)  # Replacing operating_hours_m
    close_hour = db.Column(db.String(10), nullable=False)  # Replacing operating_hours_m
    request_status = db.Column(db.String(50), default="Pending")

    def __repr__(self):
        return f'<RegistrationRequest {self.organization_name}>'