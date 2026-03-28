"""User model – thin data class."""


class User:
    def __init__(self, id, username, email, password, role):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = role  # 'admin' | 'student'

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
