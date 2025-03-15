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

# In-memory storage for our hackathon MVP
class Storage:
    def __init__(self):
        self.users = {}  # phone_number -> user_data
        self.otps = {}   # phone_number -> (otp, timestamp)
        self.issues = []  # List of issue dictionaries
        self.reviews = [] # List of review dictionaries
        self.issue_counter = 1  # Counter for generating unique issue IDs

# Create a global storage instance
storage = Storage()

# Import routes
from routes import *
