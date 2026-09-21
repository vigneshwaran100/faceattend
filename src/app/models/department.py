from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Department:
    department_id: str
    department_name: str
    created_at: datetime
    updated_at: datetime