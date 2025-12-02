class User:

    def __init__(self, username, password, role="user", maKH=None, fullName=None):
        self.username = username
        self.password = password
        self.role = role
        self.maKH = maKH
        self.fullName = fullName or username
