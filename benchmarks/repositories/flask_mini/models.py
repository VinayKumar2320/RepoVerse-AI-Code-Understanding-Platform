class DatabaseConnection:
    def __init__(self, dsn: str = "sqlite:///:memory:"):
        self.dsn = dsn
        self.connected = True

    def query(self, sql: str, params: dict = None):
        return [{"id": 1, "username": "admin", "active": True}]

class User:
    def __init__(self, id: int, username: str, active: bool = True):
        self.id = id
        self.username = username
        self.active = active
