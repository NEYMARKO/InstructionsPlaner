from sqlalchemy.orm import Session

# from ..dto.user import UserUpdate
from .user import UserRepository


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def update_profile(self, data: dict[str, str]):
        
        return