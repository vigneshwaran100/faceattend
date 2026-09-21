import logging
from datetime import datetime, timezone

from app.models.team import Team
from app.repositories.team_repository import TeamRepository

logger = logging.getLogger(__name__)


class TeamService:
    def __init__(self, repository: TeamRepository) -> None:
        self._repository = repository

    def create_team(
        self,
        *,
        team_id: str,
        team_name: str,
    ) -> Team:
        team_id = team_id.strip()
        team_name = team_name.strip()

        if not team_id:
            raise ValueError("Team ID cannot be empty")

        if not team_name:
            raise ValueError("Team name cannot be empty")

        if self._repository.exists(team_id):
            raise ValueError(
                f"Team already exists: {team_id}"
            )

        if self._repository.get_by_name(team_name):
            raise ValueError(
                f"Team name already exists: {team_name}"
            )

        now = datetime.now(timezone.utc)

        team = Team(
            team_id=team_id,
            team_name=team_name,
            created_at=now,
            updated_at=now,
        )

        created = self._repository.create(team)

        logger.info(
            "Team created successfully | team_id=%s | name=%s",
            created.team_id,
            created.team_name,
        )

        return created

    def get_team(
        self,
        team_id: str,
    ) -> Team | None:
        team_id = team_id.strip()
        if not team_id:
            raise ValueError("Team ID cannot be empty")

        return self._repository.get_by_id(team_id)

    def list_teams(self) -> list[Team]:
        return self._repository.get_all()

