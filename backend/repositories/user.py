from ..dto.user import UserDTO, UserCreationDTO

class UserRepository():
    def save_user(self, user: UserCreationDTO) -> UserDTO:
        return user