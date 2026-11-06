"""Маршрути /categories: список, створення та видалення категорій."""

from typing import Annotated

from fastapi import APIRouter, Path, status

from labs.lab03 import repository
from labs.lab03.routers import error_response, http_errors
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryId = Annotated[int, Path(gt=0, description="Ідентифікатор категорії")]


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій",
    description="Усі категорії за зростанням id.",
)
def list_categories() -> list[repository.Row]:
    return repository.list_categories()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoryRead,
    summary="Створити категорію",
    responses={409: error_response("Категорія з такою назвою вже існує")},
)
def create_category(category: CategoryCreate) -> repository.Row:
    with http_errors():
        return repository.create_category(category.name)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: error_response("Категорію не знайдено"),
        409: error_response("Категорія містить записи"),
    },
)
def delete_category(category_id: CategoryId) -> None:
    with http_errors():
        repository.delete_category(category_id)
