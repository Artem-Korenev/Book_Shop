from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from src.models.sellers import Seller
from src.models.books import Book
from icecream import ic


from src.schemas import (
    IncomingSeller,
    ReturnedAllSellers,
    ReturnedSeller,
    ReturnedSellerWithBooks,
    ReturnedBookForSeller,
    ReturnedSellerAfterCreate,
)

from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session

sellers_router = APIRouter(tags=["sellers"], prefix="/sellers")

# CRUD - Create, Read, Update, Delete

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о продавце в БД. Возвращает созданного продавца.
@sellers_router.post(
    "/", response_model=ReturnedSellerAfterCreate, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_seller(
    seller: IncomingSeller,
    session: DBSession,
):

    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    new_seller = Seller(
        **{
            "first_name": seller.first_name,
            "last_name": seller.last_name,
            "e_mail": seller.e_mail,
            "password": seller.password,
        }
    )

    session.add(new_seller)
    await session.flush()

    return new_seller


# Ручка, возвращающая всех продавцов
@sellers_router.get("/", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    result = await session.execute(query)
    sellers = result.scalars().all()
    return {"sellers": sellers}


# Ручка для получения книги по ее ИД
@sellers_router.get("/{id}", response_model=ReturnedSellerWithBooks)
async def get_seller(id: int, session: DBSession):
    if result := await session.get(Seller, id):
        query = select(Book).where(Book.seller_id == id)
        result1 = await session.execute(query)
        books = result1.scalars().all()
        # Формируем список книг в нужном формате
        returned_books = [
            ReturnedBookForSeller(
                id=book.id,
                title=book.title,
                author=book.author,
                # seller_id=book.seller_id,
                year=book.year,
                pages=book.pages,
            )
            for book in books
        ]

        # Создаем объект ReturnedSellerWithBooks
        result = ReturnedSellerWithBooks(
            first_name=result.first_name,
            last_name=result.last_name,
            e_mail=result.e_mail,
            id=result.id,
            books=returned_books,
        )

        return result
    return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для удаления продавца
@sellers_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(id: int, session: DBSession):
    deleted_seller = await session.get(Seller, id)
    if deleted_seller:
        await session.delete(deleted_seller)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для обновления данных о продавце
@sellers_router.put("/{book_id}", response_model=ReturnedSeller)
async def update_seller(
    book_id: int, new_seller_data: ReturnedSeller, session: DBSession
):
    if updated_seller := await session.get(Seller, book_id):
        updated_seller.first_name = new_seller_data.first_name
        updated_seller.last_name = new_seller_data.last_name
        updated_seller.e_mail = new_seller_data.e_mail

        await session.flush()

        return updated_seller

    return Response(status_code=status.HTTP_404_NOT_FOUND)
