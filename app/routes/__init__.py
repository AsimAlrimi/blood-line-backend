from flask import Blueprint
from .email_routes import email_bp
from .donor_routes import donor_bp
from .auth_routes import auth_bp
from .manager_routes import manager_bp
from .admin_routes import admin_bp
from .staff_routes import staff_bp

def register_routes(app):
    app.register_blueprint(email_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)