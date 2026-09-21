from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: str
    username: str
    password_hash: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
