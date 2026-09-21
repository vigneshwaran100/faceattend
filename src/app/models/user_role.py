from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    SECURITY = "security"
