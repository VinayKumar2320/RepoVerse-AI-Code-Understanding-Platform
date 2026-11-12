from flask_mini.models import DatabaseConnection, User

class UserService:
    def __init__(self, db: DatabaseConnection):
        self.db = db

    def list_active_users(self):
        rows = self.db.query("SELECT * FROM users WHERE active = 1")
        return [User(r["id"], r["username"], r["active"]) for r in rows]

    def authenticate(self, creds: dict):
        if creds.get("username") == "admin":
            return {"authenticated": True, "token": "xyz123"}
        return {"authenticated": False, "error": "Invalid username"}
