from app import db

class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(200), nullable=False, unique=True)

    def __repr__(self):
        return f'<Blacklist {self.jti}>'