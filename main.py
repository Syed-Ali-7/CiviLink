from app import app
from database import init_db

if __name__ == "__main__":
    init_db()  # Initialize database tables
    app.run(host="0.0.0.0", port=5000, debug=True)
