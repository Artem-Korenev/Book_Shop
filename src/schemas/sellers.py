from pydantic import BaseModel, Field, field_validator
from .books import ReturnedBookForSeller


__all__ = [
    "IncomingSeller",
    "ReturnedSeller",
    "ReturnedAllSellers",
    "ReturnedSellerWithBooks",
    "ReturnedSellerAfterCreate",
]


# Базовый класс "Продавца", содержащий поля, которые есть во всех классах-наследниках.
class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    e_mail: str


# Класс для валидации входящих данных. Не содержит id, так как его присваивает БД.
class IncomingSeller(BaseSeller):
    password: str


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedSeller(BaseSeller):
    id: int


# Класс для возврата массива объектов "Продавец"
class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]


# Класс для возврата продавца после его создания
class ReturnedSellerAfterCreate(BaseSeller):
    id: int
    password: str


# Класс для возврата конкретного продавца вместе с его книгами
class ReturnedSellerWithBooks(BaseSeller):
    id: int
    books: list[ReturnedBookForSeller]
