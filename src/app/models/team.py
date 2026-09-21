from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Team:
    team_id: str
    team_name: str
    created_at: datetime
    updated_at: datetime