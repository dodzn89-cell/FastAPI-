import httpx
import pytest
from fastapi import status

from app.models.users import UserModel
from app.schemas.users import GenderEnum
from main import app


@pytest.mark.asyncio
async def test_api_create_user() -> None:
    data = {"username": "testuser", "age": 20, "gender": "male"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(url="/users", json=data)

    assert response.status_code == status.HTTP_200_OK
    created_user_id = response.json()

    created_user = UserModel.filter(id=created_user_id)[0]
    assert created_user.username == "testuser"
    assert created_user.age == 20
    assert created_user.gender == GenderEnum.male


@pytest.mark.asyncio
async def test_api_get_all_users() -> None:
    UserModel.create_dummy()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(url="/users")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == len(UserModel._data)
    assert data[0]["id"] == UserModel._data[0].id
    assert data[0]["username"] == UserModel._data[0].username
    assert data[0]["age"] == UserModel._data[0].age
    assert data[0]["gender"] == UserModel._data[0].gender


@pytest.mark.asyncio
async def test_api_get_all_users_when_user_not_found() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(url="/users")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_get_user() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(url="/users", json={"username": "testuser", "age": 20, "gender": "male"})
        user_id = create_response.json()
        user = UserModel.get(id=user_id)
        assert user is not None

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(url=f"/users/{user_id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "testuser"
    assert data["age"] == 20
    assert data["gender"] == "male"


@pytest.mark.asyncio
async def test_api_get_user_when_user_not_found() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(url="/users/999999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_update_user() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(url="/users", json={"username": "testuser", "age": 20, "gender": "male"})
        user_id = create_response.json()
        assert UserModel.get(id=user_id) is not None

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            url=f"/users/{user_id}",
            json={"username": "updated_username", "age": 30},
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "updated_username"
    assert data["age"] == 30
    assert data["gender"] == "male"


@pytest.mark.asyncio
async def test_api_update_user_when_user_not_found() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(url="/users/999999999", json={"username": "x"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_delete_user() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(url="/users", json={"username": "testuser", "age": 20, "gender": "male"})
        user_id = create_response.json()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(url=f"/users/{user_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == f"User: {user_id}, Successfully Deleted."
    assert UserModel.get(id=user_id) is None


@pytest.mark.asyncio
async def test_api_delete_user_when_user_not_found() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(url="/users/999999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_search_users() -> None:
    # given
    UserModel.create(username="alice", age=20, gender=GenderEnum.female)
    UserModel.create(username="bob", age=30, gender=GenderEnum.male)
    UserModel.create(username="alice", age=20, gender=GenderEnum.female)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/search?username=alice&age=20&gender=female")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert all(u["username"] == "alice" for u in data)
    assert all(u["age"] == 20 for u in data)
    assert all(u["gender"] == "female" for u in data)


@pytest.mark.asyncio
async def test_api_search_users_when_not_found() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/search?username=nope&age=20&gender=male")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_api_search_users_rejects_extra_query_params() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/users/search?username=alice&age=20&gender=female&extra=1")

    # extra forbid가 동작하면 보통 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
