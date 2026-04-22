from app.core import security
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError
from app.repositories.users import UserRepository
from app.schemas.user import UserPublic


class AuthUseCase:
    
    def __init__(self, repo: UserRepository):
        self.repo = repo


    async def register(self, email: str, password: str) -> UserPublic:
        if await self.repo.get_by_email(email):
            raise UserAlreadyExistsError()
        
        hashed = security.hash_password(password)
        user = await self.repo.create(email, hashed)
        return UserPublic.model_validate(user)


    async def login(self, email: str, password: str) -> str:
        user = await self.repo.get_by_email(email)
        if not user or not security.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        payload = {"sub": str(user.id), "role": user.role}
        return security.create_access_token(payload)


    async def get_me(self, user_id: int) -> UserPublic:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return UserPublic.model_validate(user)
    