from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_uc, get_current_user_id
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.usecases.auth import AuthUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
):
    return await uc.register(data.email, data.password)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
):
    token = await uc.login(form.username, form.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def get_me(
    user_id: Annotated[int, Depends(get_current_user_id)],
    uc: Annotated[AuthUseCase, Depends(get_auth_uc)],
):
    return await uc.get_me(user_id)
