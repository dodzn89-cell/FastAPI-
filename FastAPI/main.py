from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request

from app.models.users import UserModel
from app.schemas.users import (
    GenderEnum,
    UserCreateRequest,
    UserResponse,
    UserSearchQuery,
    UserUpdateRequest,
)

app = FastAPI()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ok"}


# 1. 유저 생성
@app.post("/users")
async def create_user(data: UserCreateRequest) -> int:
    user = UserModel.create(**data.model_dump())
    return user.id


# 2. 유저 검색 (Query + Pydantic + extra query 차단)
def validate_search_query(
    request: Request,
    username: str = Query(...),
    age: int = Query(..., gt=0),
    gender: GenderEnum = Query(...),
) -> UserSearchQuery:
    allowed = {"username", "age", "gender"}
    extra = set(request.query_params.keys()) - allowed
    if extra:
        raise HTTPException(status_code=422)

    return UserSearchQuery(username=username, age=age, gender=gender)


@app.get("/users/search", response_model=list[UserResponse])
async def search_users(
    query: UserSearchQuery = Depends(validate_search_query),
) -> list[UserModel]:
    users = UserModel.filter(**query.model_dump())
    if not users:
        raise HTTPException(status_code=404)
    return users


# 3. 모든 유저 조회
@app.get("/users", response_model=list[UserResponse])
async def get_all_users() -> list[UserModel]:
    users = UserModel.all()
    if not users:
        raise HTTPException(status_code=404)
    return users


# 4. 특정 유저 조회
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int = Path(gt=0)) -> UserModel:
    user = UserModel.get(id=user_id)
    if user is None:
        raise HTTPException(status_code=404)
    return user


# 5. 유저 부분 수정
@app.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    data: UserUpdateRequest,
    user_id: int = Path(gt=0),
) -> UserModel:
    user = UserModel.get(id=user_id)
    if user is None:
        raise HTTPException(status_code=404)

    user.update(**data.model_dump(exclude_none=True))
    return user


# 6. 유저 삭제
@app.delete("/users/{user_id}")
async def delete_user(user_id: int = Path(gt=0)) -> dict[str, str]:
    user = UserModel.get(id=user_id)
    if user is None:
        raise HTTPException(status_code=404)

    user.delete()
    return {"detail": f"User: {user_id}, Successfully Deleted."}
