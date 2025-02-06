from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.roles import get_role_service, list_roles_service
from schemas.roles_schemas import RoleResponse, RolesListResponse
from shared.database.db_session import get_db_account


router = APIRouter(tags=["roles"])


@router.get("/{role_id}", response_model=RoleResponse)
def get_role_route(role_id: int, db: Session = Depends(get_db_account)):
    try:
        return get_role_service.execute(db, role_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting role",
        )


@router.get("/", response_model=RolesListResponse)
def list_roles_route(db: Session = Depends(get_db_account)):
    try:
        return list_roles_service.execute(db)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing roles",
        )
