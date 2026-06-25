from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.orm import Session

from ..dto.user import UserDTO, UserCreationDTO
from ..services.user import UserService
from ..db import get_db

router = APIRouter(prefix="/users")
service = UserService()

@router.get("/{id}")
async def get_user(id: int):
    return {"id": id}

@router.post("/create")
async def create_user(user: UserCreationDTO, db: Annotated[Session, Depends(get_db)]) -> UserDTO:
    return service.create_user(user, db)