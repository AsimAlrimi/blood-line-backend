import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from dotenv import load_dotenv

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

def create_app():
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # Basic config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 3600  # 24 hours in seconds

    # Email config
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USERNAME')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    with app.app_context():

        from app import models  
        from app import commands 
        from app.routes import register_routes
        register_routes(app)

    return app
