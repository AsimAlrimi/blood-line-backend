import os
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from app import db
from app.models.users import Admin
  
@current_app.cli.command("create-admin")
@with_appcontext
def create_admin():

    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not admin_email or not admin_password:
        print("Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env file.")
        return

    max_admin_id = Admin.query.filter(Admin.id.between(1, 9999)).order_by(Admin.id.desc()).first()
    next_admin_id = (max_admin_id.id + 1) if max_admin_id else 1 

    if not Admin.query.filter_by(email=admin_email).first():
        admin = Admin(
            id=next_admin_id,
            username='Admin',
            email=admin_email,
            password=generate_password_hash(admin_password),
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user {admin_email} created successfully.")
    else:
        print(f"Admin user {admin_email} already exists.")
