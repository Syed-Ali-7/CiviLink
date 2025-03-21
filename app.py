import os
import logging
import base64
from datetime import datetime
from flask import Flask
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Setup LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Storage:
    def __init__(self):
        self.users = {}  # phone_number -> user_data
        self.otps = {}   # phone_number -> (otp, timestamp)
        self.reviews = [] # List of review dictionaries
        self.issues = [] # List of issue dictionaries
        self.issue_counter = 1  # Counter for generating unique issue IDs
        self.departments = [
            "Solid Waste Management",
            "Road Infrastructure",
            "Water Supply",
            "Sewage and Drainage",
            "Horticulture",
            "Health",
            "Engineering",
            "Town Planning"
        ]
        self.wards = [
            "Yelahanka", "Byatarayanapura", "Kodigehalli", "Hebbal",
            "Kempapura", "Malleswaram", "Jayamahal", "Vasanth Nagar",
            "Shivajinagar", "Domlur", "Indira Nagar", "HSR Layout",
            "Bellandur", "Jayanagar", "JP Nagar"
        ]
        self.issue_types = [
            "Road Damage", "Garbage Collection", "Streetlight Issue",
            "Water Supply Problem", "Sewage Overflow", "Illegal Construction",
            "Park Maintenance", "Public Toilet Issue", "Stray Animal Concern",
            "Tree Hazard"
        ]
        self._initialize_officers()

    def _initialize_officers(self):
        has_officers = any(user.get('role') == 'officer' for user in self.users.values())
        if not has_officers:
            officers = [
                {
                    'phone': '9876543210',
                    'name': 'Rajesh Kumar',
                    'ward': 'Jayanagar',
                    'role': 'officer',
                    'employee_id': 'BBMP001',
                    'department': 'Solid Waste Management',
                    'verified': True
                },
                {
                    'phone': '9876543211',
                    'name': 'Priya Sharma',
                    'ward': 'HSR Layout',
                    'role': 'officer',
                    'employee_id': 'BBMP002',
                    'department': 'Road Infrastructure',
                    'verified': True
                },
                {
                    'phone': '9876543212',
                    'name': 'Suresh Reddy',
                    'ward': 'Indira Nagar',
                    'role': 'admin',
                    'employee_id': 'BBMP003',
                    'department': 'Engineering',
                    'verified': True
                }
            ]
            for officer in officers:
                self.users[officer['phone']] = officer

    def assign_issue(self, issue_id, officer_id):
        for issue in self.issues:
            if issue['id'] == issue_id:
                issue['assigned_to'] = officer_id
                issue['assigned_time'] = datetime.now().isoformat()
                issue['status'] = 'ongoing'
                issue['status_updated'] = True
                return True
        return False

    def get_officers_by_department(self, department=None):
        officers = []
        for user_id, user_data in self.users.items():
            if user_data.get('role') in ['officer', 'admin']:
                if department is None or user_data.get('department') == department:
                    officers.append(user_data)
        return officers

    def get_department_issues(self, department):
        return [issue for issue in self.issues if issue.get('department') == department]

    def get_officer_issues(self, officer_id):
        return [issue for issue in self.issues if issue.get('assigned_to') == officer_id]

    def get_ward_issues(self, ward):
        return [issue for issue in self.issues if issue.get('ward') == ward]

# Create a global storage instance
storage = Storage()

# Import routes
from routes import *