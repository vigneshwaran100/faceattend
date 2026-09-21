import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_team_service,
    require_admin,
    require_authenticated,
)
from app.api.schemas.team import (
    TeamCreateRequest,
    TeamResponse,
)
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.services.team_service import TeamService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/teams",
    tags=["Teams"],
)


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    request: TeamCreateRequest,
    service: TeamService = Depends(get_team_service),
    current_user: User = Depends(require_admin),
) -> TeamResponse:
    try:
        team = service.create_team(
            team_id=request.team_id,
            team_name=request.team_name,
        )

        return TeamResponse(
            team_id=team.team_id,
            team_name=team.team_name,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error creating team | error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.get(
    "",
    response_model=list[TeamResponse],
)
def list_teams(
    service: TeamService = Depends(get_team_service),
    current_user: User = Depends(require_authenticated),
) -> list[TeamResponse]:
    try:
        teams = service.list_teams()

        return [
            TeamResponse(
                team_id=team.team_id,
                team_name=team.team_name,
                created_at=team.created_at,
                updated_at=team.updated_at,
            )
            for team in teams
        ]

    except DatabaseError as error:
        logger.error(
            "Database error listing teams | error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
)
def get_team(
    team_id: str,
    service: TeamService = Depends(get_team_service),
    current_user: User = Depends(require_authenticated),
) -> TeamResponse:
    try:
        team = service.get_team(team_id)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team not found: {team_id}",
            )

        return TeamResponse(
            team_id=team.team_id,
            team_name=team.team_name,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error getting team | team_id=%s | error=%s",
            team_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

