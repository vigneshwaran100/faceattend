from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models.department import DepartmentORM
from app.database.models.employee import EmployeeORM
from app.database.models.team import TeamORM
from app.models.team import Team
from app.repositories.team_repository import TeamRepository


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    return Session(engine)


def create_team() -> Team:
    now = datetime.now(timezone.utc)

    return Team(
        team_id="TEAM001",
        team_name="AI Team",
        created_at=now,
        updated_at=now,
    )


def test_create_team() -> None:
    session = create_test_session()

    repository = TeamRepository(session)

    team = create_team()

    result = repository.create(team)

    assert result.team_id == "TEAM001"
    assert result.team_name == "AI Team"


def test_get_by_id() -> None:
    session = create_test_session()

    repository = TeamRepository(session)

    repository.create(create_team())

    result = repository.get_by_id("TEAM001")

    assert result is not None
    assert result.team_id == "TEAM001"


def test_get_by_id_returns_none_for_missing_team() -> None:
    session = create_test_session()

    repository = TeamRepository(session)

    result = repository.get_by_id("UNKNOWN")

    assert result is None


def test_exists() -> None:
    session = create_test_session()

    repository = TeamRepository(session)

    repository.create(create_team())

    assert repository.exists("TEAM001") is True
    assert repository.exists("UNKNOWN") is False


def test_get_all() -> None:
    session = create_test_session()
    repository = TeamRepository(session)

    assert repository.get_all() == []

    repository.create(create_team())
    teams = repository.get_all()
    assert len(teams) == 1
    assert teams[0].team_id == "TEAM001"