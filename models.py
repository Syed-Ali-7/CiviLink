from flask_login import UserMixin
from app import login_manager, storage

class User(UserMixin):
    def __init__(self, id, phone, name=None, ward=None):
        self.id = id  # Using phone number as ID
        self.phone = phone
        self.name = name
        self.ward = ward
        self.issues_reported = 0
        self.stars = 0  # Rewards for active users

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    if user_id in storage.users:
        user_data = storage.users[user_id]
        user = User(
            id=user_id,
            phone=user_data['phone'],
            name=user_data.get('name'),
            ward=user_data.get('ward')
        )
        user.issues_reported = user_data.get('issues_reported', 0)
        user.stars = user_data.get('stars', 0)
        return user
    return None
