"""
Mini Flask-like Application fixture for testing & benchmarking.
"""
from flask_mini.services import UserService
from flask_mini.models import DatabaseConnection

class Application:
    def __init__(self, name: str):
        self.name = name
        self.db = DatabaseConnection()
        self.user_service = UserService(self.db)

    def route(self, path: str):
        def decorator(f):
            return f
        return decorator

app = Application("MiniApp")

@app.route("/api/v1/users")
def get_users_endpoint():
    """Retrieve list of registered users."""
    return app.user_service.list_active_users()

@app.route("/api/v1/login")
def login_endpoint(credentials: dict):
    """Authenticate incoming user request."""
    return app.user_service.authenticate(credentials)
