from flask_login import UserMixin
from app import login_manager, storage

# Define user roles
ROLE_CITIZEN = 'citizen'
ROLE_OFFICER = 'officer'
ROLE_ADMIN = 'admin'

class User(UserMixin):
    def __init__(self, id, phone, name=None, ward=None, role=ROLE_CITIZEN, employee_id=None, department=None):
        self.id = id  # Using phone number as ID
        self.phone = phone
        self.name = name
        self.ward = ward
        self.role = role
        self.employee_id = employee_id
        self.department = department
        self.issues_reported = 0
        self.issues_resolved = 0
        self.stars = 0  # Rewards for active users

    def get_id(self):
        return self.id
    
    def is_officer(self):
        return self.role in [ROLE_OFFICER, ROLE_ADMIN]
    
    def is_admin(self):
        return self.role == ROLE_ADMIN

@login_manager.user_loader
def load_user(user_id):
    if user_id in storage.users:
        user_data = storage.users[user_id]
        user = User(
            id=user_id,
            phone=user_data['phone'],
            name=user_data.get('name'),
            ward=user_data.get('ward'),
            role=user_data.get('role', ROLE_CITIZEN),
            employee_id=user_data.get('employee_id'),
            department=user_data.get('department')
        )
        user.issues_reported = user_data.get('issues_reported', 0)
        user.issues_resolved = user_data.get('issues_resolved', 0)
        user.stars = user_data.get('stars', 0)
        return user
    return None
