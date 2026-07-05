from fastapi import APIRouter, HTTPException, Request, Response

from app.api.deps import SESSION_COOKIE, AuthServiceDep, CurrentUserDep, SettingsDep
from app.core.config import Settings
from app.domain.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import InvalidCredentialsError, UsernameTakenError

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest, response: Response, auth_service: AuthServiceDep, settings: SettingsDep
) -> UserResponse:
    try:
        user = auth_service.register(body.username, body.password)
    except UsernameTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    token = auth_service.create_session(user.id)
    _set_session_cookie(response, token, settings)
    return UserResponse(**user.model_dump())


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest, response: Response, auth_service: AuthServiceDep, settings: SettingsDep
) -> UserResponse:
    try:
        user = auth_service.authenticate(body.username, body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    token = auth_service.create_session(user.id)
    _set_session_cookie(response, token, settings)
    return UserResponse(**user.model_dump())


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, auth_service: AuthServiceDep) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        auth_service.delete_session(token)
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> UserResponse:
    return UserResponse(**user.model_dump())
