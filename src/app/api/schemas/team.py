from datetime import datetime

from pydantic import BaseModel


class TeamCreateRequest(BaseModel):
    team_id: str
    team_name: str


class TeamResponse(BaseModel):
    team_id: str
    team_name: str
    created_at: datetime
    updated_at: datetime
