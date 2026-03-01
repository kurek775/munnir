from fastapi import APIRouter

from app.api.v1.endpoints import auth, execution, hello, news, sessions, users

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(hello.router, tags=["hello"])
v1_router.include_router(auth.router, tags=["auth"])
v1_router.include_router(users.router, tags=["users"])
v1_router.include_router(sessions.router, tags=["sessions"])
v1_router.include_router(news.router, tags=["news"])
v1_router.include_router(execution.router, tags=["execution"])
