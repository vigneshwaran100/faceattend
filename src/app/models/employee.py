from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Employee:
    employee_id: str
    name: str
    email: str
    team_id: str
    department_id: str | None
    designation: str | None
    status: str
    created_at: datetime
    updated_at: datetime