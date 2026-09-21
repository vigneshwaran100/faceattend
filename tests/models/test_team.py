from datetime import datetime, timezone

from app.models.team import Team


def test_team_creation() -> None:
    now = datetime.now(timezone.utc)

    team = Team(
        team_id="TEAM001",
        team_name="AI Team",
        created_at=now,
        updated_at=now,
    )

    assert team.team_id == "TEAM001"
    assert team.team_name == "AI Team"