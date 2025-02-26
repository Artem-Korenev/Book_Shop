import pytest
from sqlalchemy import select
from src.models.books import Book
from src.models.sellers import Seller
from fastapi import status
from icecream import ic
import pytest_asyncio


# Создание фикстуры для записи одного продавца в БД
@pytest_asyncio.fixture(scope="function")
async def seller_fixture(async_client):
    # Добавляем продавца перед выполнением тестов
    data = {
        "first_name": "Artyom",
        "last_name": "Artyom",
        "e_mail": "Artyom",
        "password": "Artyom",
    }
    response = await async_client.post("/api/v1/sellers/", json=data)
    assert response.status_code == 201
    seller_id = response.json()["id"]
    return seller_id


# Тест на ручку, создающую книгу
@pytest.mark.asyncio
async def test_create_book(async_client, seller_fixture):
    data = {
        "title": "Clean Architecture",
        "author": " Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller_fixture,
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id, "Book id not returned from endpoint"

    assert result_data == {
        "title": "Clean Architecture",
        "author": " Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": seller_fixture,
    }


# Тест на ручку, создающую книгу старого года издания
@pytest.mark.asyncio
async def test_create_book_with_old_year(async_client, seller_fixture):

    data = {
        "title": "Clean Architecture",
        "author": " Robert Martin",
        "count_pages": 300,
        "year": 1025,
        "seller_id": seller_fixture,
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio
async def test_get_books(db_session, async_client, seller_fixture):
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=seller_fixture,
    )
    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=2023,
        pages=104,
        seller_id=seller_fixture,
    )

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/books/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["books"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": seller_fixture,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2023,
                "id": book_2.id,
                "pages": 104,
                "seller_id": seller_fixture,
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio
async def test_get_single_book(db_session, async_client, seller_fixture):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке

    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=seller_fixture,
    )
    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=2023,
        pages=104,
        seller_id=seller_fixture,
    )

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2021,
        "pages": 104,
        "id": book.id,
        "seller_id": seller_fixture,
    }


# Тест на ручку обновления книги
@pytest.mark.asyncio
async def test_update_book(db_session, async_client, seller_fixture):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=seller_fixture,
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/books/{book.id}",
        json={
            "title": "Mziri",
            "author": "Lermontov",
            "pages": 100,
            "year": 2007,
            "id": book.id,
            "seller_id": seller_fixture,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 100
    assert res.year == 2007
    assert res.id == book.id
    assert res.seller_id == book.seller_id


# Тест на ручку удаления книги
@pytest.mark.asyncio
async def test_delete_book(db_session, async_client, seller_fixture):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=seller_fixture,
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


# Тест на ручку удаления книги с несуществующим id
@pytest.mark.asyncio
async def test_delete_book_with_invalid_book_id(
    db_session, async_client, seller_fixture
):
    book = Book(
        author="Lermontov",
        title="Mtziri",
        pages=510,
        year=2024,
        seller_id=seller_fixture,
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/books/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
