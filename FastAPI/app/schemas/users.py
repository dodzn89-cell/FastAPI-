from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class UserCreateRequest(BaseModel):
    username: str
    age: int
    gender: GenderEnum


class UserUpdateRequest(BaseModel):
    username: str | None = None
    age: int | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    age: int
    gender: GenderEnum


class UserSearchQuery(BaseModel):
    # username/age/gender 외 쿼리 받으면 에러
    model_config = ConfigDict(extra="forbid")

    username: str
    age: int = Field(gt=0)  # age > 0
    gender: GenderEnum
