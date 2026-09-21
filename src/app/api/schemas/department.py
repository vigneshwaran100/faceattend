from datetime import datetime

from pydantic import BaseModel


class DepartmentCreateRequest(BaseModel):
    department_id: str
    department_name: str


class DepartmentResponse(BaseModel):
    department_id: str
    department_name: str
    created_at: datetime
    updated_at: datetime
