from app import db
from datetime import datetime 

class EmailVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(5), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    