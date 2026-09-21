from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.team import TeamORM
from app.models.team import Team


class TeamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, team: Team) -> Team:
        entity = TeamORM(
            team_id=team.team_id,
            team_name=team.team_name,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

        self._session.add(entity)
        self._session.flush()

        return self._to_domain(entity)

    def get_by_id(self, team_id: str) -> Team | None:
        statement = select(TeamORM).where(
            TeamORM.team_id == team_id
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    def exists(self, team_id: str) -> bool:
        statement = select(TeamORM.team_id).where(
            TeamORM.team_id == team_id
        )

        return self._session.scalar(statement) is not None

    def get_all(self) -> list[Team]:
        statement = select(TeamORM).order_by(
            TeamORM.team_id
        )

        entities = self._session.scalars(statement).all()

        return [self._to_domain(entity) for entity in entities]

    def get_by_name(
        self,
        team_name: str,
    ) -> Team | None:
        statement = select(TeamORM).where(
            TeamORM.team_name == team_name
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    @staticmethod
    def _to_domain(entity: TeamORM) -> Team:
        return Team(
            team_id=entity.team_id,
            team_name=entity.team_name,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )