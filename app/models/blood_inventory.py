from app import db

class BloodInventory(db.Model):
    Inventory_ID = db.Column(db.Integer, primary_key=True)
    blood_bank_ID = db.Column(db.Integer, db.ForeignKey('blood_bank.blood_bank_id'), nullable=False)
    Blood_Type = db.Column(db.String(100), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False) # By unit, the unit (450 ml to 500 ml) whole blood
    Expiration_Date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<BloodInventory {self.Blood_Type}>'
    