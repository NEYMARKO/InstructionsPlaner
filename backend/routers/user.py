from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session

from ..dto.user import UserDTO, UserCreationDTO
from ..services.user import UserService
from ..db import get_db

router = APIRouter(prefix="/users")
service = UserService()

@router.get("/")
async def get_users(db: Annotated[Session, Depends(get_db)]) -> list[UserDTO]:
    return service.get_users(db)

@router.post("/create")
async def create_user(user: UserCreationDTO, db: Annotated[Session, Depends(get_db)]) -> UserDTO:
    return service.create_user(user, db)