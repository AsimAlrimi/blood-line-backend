# Blood Line

**A Comprehensive Blood Donation Management System**

Blood Line is a platform designed to streamline the blood donation process, enhance communication among stakeholders, and optimize blood bank operations. The system consists of:
- **[Mobile App](https://github.com/AsimAlrimi/blood-line-mobile.git)**  
- **[Desktop App](https://github.com/AsimAlrimi/blood-line-desktop.git)**  
- **Backend**  

The backend serves as the core of the Blood Line system, providing secure API endpoints for mobile and desktop applications. It manages user authentication, data storage, notifications, and system-wide operations.

---

## Blood Line Backend

### Overview
The Blood Line Backend is built using Flask and provides RESTful APIs to support the functionalities of the mobile and desktop applications. It handles authentication, blood donation management, notifications, and data storage, ensuring smooth communication between all system components.

### Tech Stack
- **Framework:** Flask (Python)
- **Database:** SQLite
- **Authentication:** JWT (JSON Web Token)
- **Email Services:** Flask-Mail (SMTP)
- **Environment Management:** dotenv

---

## Features

### **Authentication & Security**
- **User Authentication:** Secure login and registration using JWT tokens.
- **Role-Based Access Control:** Different access levels for admins, managers, staff, and donors.
- **Password Reset:** Email-based password recovery system.

### **Blood Donation Management**
- **Donor Management:** Maintain donor records and history.
- **Appointment Scheduling:** API for donors to book and manage donation appointments.
- **Blood Inventory Tracking:** Real-time monitoring of blood stock levels.

### **Communication & Notifications**
- **Email Notifications:** Automatic email alerts for upcoming appointments and urgent blood needs.
- **System Alerts:** Push notifications for mobile and desktop users.

### **Admin & Data Management**
- **Admin Panel Support:** Provides APIs for dashboard statistics and user management.
- **Data Analytics:** Tracks donation trends and generates statistical insights.
- **Organization Approval System:** Admins can accept or reject blood bank registration requests.

---

## Getting Started

### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Virtual Environment (venv)

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/AsimAlrimi/Blood_Line-Server-.git
   ```
2. Navigate to the project directory:
   ```sh
   cd Blood_Line-Server-
   ```
3. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Set up environment variables (create a `.env` file in the root directory):
   ```
   SQLALCHEMY_DATABASE_URI=<your_database_uri>
   SECRET_KEY=<your_secret_key>
   JWT_SECRET_KEY=<your_jwt_secret>
   EMAIL_USERNAME=<your_email>
   EMAIL_PASSWORD=<your_email_password>
   ```
6. Initialize the database:
   ```sh
   python create_db.py
   ```
7. Run the application:
   ```sh
   flask run
   ```
