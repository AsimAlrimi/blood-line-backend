from app import db

class Disease(db.Model):
    disease_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Disease {self.name}>'
    
class DonorDisease(db.Model):
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id'), primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.disease_id'), primary_key=True)