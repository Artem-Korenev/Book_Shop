import pytest
from sqlalchemy import select
from src.models.books import Book
from src.models.sellers import Seller
from fastapi import status
from icecream import ic


# Тест на ручку, создающую продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):

    data = {
        "first_name": "Artyom",
        "last_name": "Korenev",
        "e_mail": "Artyom@mail.ru",
        "password": "Art",
    }
    response = await async_client.post("/api/v1/sellers/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_seller_id = result_data.pop("id", None)
    assert resp_seller_id, "Seller id not returned from endpoint"

    assert result_data == {
        "first_name": "Artyom",
        "last_name": "Korenev",
        "e_mail": "Artyom@mail.ru",
        "password": "Art",
    }


# Тест на ручку получения списка продавцов
@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller_1 = Seller(
        first_name="Artyom",
        last_name="Korenev",
        e_mail="Artyom@mail.ru",
        password="Art",
    )

    seller_2 = Seller(
        first_name="Sergey",
        last_name="Sergeev",
        e_mail="Sergey@mail.ru",
        password="Serg",
    )

    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/sellers/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["sellers"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "sellers": [
            {
                "first_name": "Artyom",
                "last_name": "Korenev",
                "e_mail": "Artyom@mail.ru",
                "id": seller_1.id,
            },
            {
                "first_name": "Sergey",
                "last_name": "Sergeev",
                "e_mail": "Sergey@mail.ru",
                "id": seller_2.id,
            },
        ]
    }


# Тест на ручку обновления продавца
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(
        first_name="Artyom",
        last_name="Korenev",
        e_mail="Artyom@mail.ru",
        password="Art",
    )
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/sellers/{seller.id}",
        json={
            "first_name": "Sergey",
            "last_name": "Sergeev",
            "e_mail": "Sergey@mail.ru",
            "id": seller.id,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Seller, seller.id)
    assert res.first_name == "Sergey"
    assert res.last_name == "Sergeev"
    assert res.e_mail == "Sergey@mail.ru"
    assert res.id == seller.id


# Тест на ручку удаления продавца
@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = Seller(
        first_name="Artyom",
        last_name="Korenev",
        e_mail="Artyom@mail.ru",
        password="Art",
    )

    db_session.add(seller)
    await db_session.flush()
    ic(seller.id)

    response = await async_client.delete(f"/api/v1/sellers/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_sellers = await db_session.execute(select(Seller))
    res = all_sellers.scalars().all()

    assert len(res) == 0


# Тест на ручку получения одного продавца
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    # Создаем книги и продавцов вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    book_1 = Book(
        title="Clean Architecture",
        author="Robert Martin",
        year=2025,
        pages=300,
        id=1,
    )

    book_2 = Book(
        title="Clean Architecture2",
        author="Robert Martin2",
        year=2023,
        pages=350,
        id=2,
    )

    seller_1 = Seller(
        first_name="Artyom",
        last_name="Korenev",
        e_mail="Artyom@mail.ru",
        password="Art",
        book_back=[book_1],
    )

    seller_2 = Seller(
        first_name="Sergey",
        last_name="Sergeev",
        e_mail="Sergey@mail.ru",
        password="Serg",
        book_back=[book_2],
    )

    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.get(f"/api/v1/sellers/{seller_1.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "first_name": "Artyom",
        "last_name": "Korenev",
        "e_mail": "Artyom@mail.ru",
        "id": seller_1.id,
        "books": [
            {
                "title": "Clean Architecture",
                "author": "Robert Martin",
                "year": 2025,
                "pages": 300,
                "id": 1,
            },
        ],
    }


# Тест на ручку удаления продавца с некорретным id
@pytest.mark.asyncio
async def test_delete_seller_with_invalid_seller_id(db_session, async_client):

    seller = Seller(
        first_name="Artyom",
        last_name="Korenev",
        e_mail="Artyom@mail.ru",
        password="Art",
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/sellers/{seller.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
