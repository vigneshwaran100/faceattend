from datetime import datetime

from pydantic import BaseModel, EmailStr


class EmployeeCreateRequest(BaseModel):
    employee_id: str
    name: str
    email: EmailStr
    team_id: str
    department_id: str | None = None
    designation: str | None = None


class EmployeeUpdateRequest(BaseModel):
    name: str
    email: EmailStr
    team_id: str
    department_id: str | None = None
    designation: str | None = None
    status: str = "active"


class EmployeeStatusUpdateRequest(BaseModel):
    status: str


class EmployeeResponse(BaseModel):
    employee_id: str
    name: str
    email: str
    team_id: str
    department_id: str | None
    designation: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class FaceEnrollmentResponse(BaseModel):
    employee_id: str
    message: str


class FaceSamplesEnrollmentResponse(BaseModel):
    employee_id: str
    samples_received: int
    embeddings_stored: int
    enrollment_status: str
    message: str