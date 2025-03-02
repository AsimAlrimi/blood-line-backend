from app import db

from .users import User, Donor, Admin, Manager, StaffMember
from .email_verification import EmailVerification
from .appointment import Appointment
from .blacklist import Blacklist
from .blood_bank import BloodBank, DonorBloodBank
from .blood_donation import BloodDonation
from .blood_inventory import BloodInventory
from .blood_need import BloodNeed
from .disease import Disease, DonorDisease
from .event import Event
from .faq import FAQ
from .registration_request import RegistrationRequest
from .volunteering import Volunteering

__all__ = [
    "User", "Donor", "Admin", "Manager", "StaffMember",
    "EmailVerification", "Appointment", "Blacklist",
    "BloodBank", "DonorBloodBank", "BloodDonation", "BloodInventory",
    "BloodNeed", "Disease", "DonorDisease", "Event", "FAQ",
    "RegistrationRequest", "Volunteering"
]
