from fastapi import APIRouter
from ..dto.user import UserDTO, UserCreationDTO
from ..services.user import UserService

router = APIRouter(prefix="/users")
service = UserService()

@router.get("/{id}")
async def get_user(id: int):
    return {"id": id}

@router.post("/create")
async def create_user(user: UserCreationDTO) -> UserDTO:
    return service.create_user(user)