"""Маршрути /records: CRUD, фільтрація та пакетне створення записів."""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, status

from labs.lab03 import repository
from labs.lab03.config import THRESHOLD, UNIT, VALUE_MIN
from labs.lab03.routers import error_response, http_errors
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace, Status

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]

RECORD_NOT_FOUND = error_response("Запис не знайдено")
CATEGORY_NOT_FOUND = error_response("Категорію запису не знайдено")
CODE_CONFLICT = error_response("Запис з таким code вже існує")


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів із фільтрами",
    description="Фільтри об'єднуються через AND, результат відсортовано за id.",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    record_status: Annotated[
        Status | None, Query(alias="status", description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=VALUE_MIN,
            allow_inf_nan=False,
            description=f"value >= min_value, {UNIT}; поріг варіанта — {THRESHOLD}",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title, з урахуванням регістру",
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Максимальна кількість записів")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Скільки записів пропустити")] = 0,
) -> list[repository.Row]:
    return repository.list_records(
        category_id=category_id,
        status=record_status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RecordRead,
    summary="Створити запис",
    responses={404: CATEGORY_NOT_FOUND, 409: CODE_CONFLICT},
)
def create_record(record: RecordCreate) -> repository.Row:
    with http_errors():
        return repository.create_record(record.model_dump())


@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED,
    response_model=list[RecordRead],
    summary="Пакетно створити записи",
    description="Усі записи зберігаються в одній транзакції: або всі, або жоден.",
    responses={
        404: CATEGORY_NOT_FOUND,
        409: error_response("Дублікат code у базі або всередині пакета"),
    },
)
def create_records_bulk(
    records: Annotated[
        list[RecordCreate],
        Body(min_length=1, max_length=100, description="Від 1 до 100 записів"),
    ],
) -> list[repository.Row]:
    with http_errors():
        return repository.create_records_bulk(
            [record.model_dump() for record in records]
        )


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис",
    responses={404: RECORD_NOT_FOUND},
)
def get_record(record_id: RecordId) -> repository.Row:
    with http_errors():
        return repository.get_record(record_id)


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити запис",
    description="Потрібні всі змінювані поля; id запису не змінюється.",
    responses={
        404: error_response("Запис або його категорію не знайдено"),
        409: CODE_CONFLICT,
    },
)
def replace_record(record_id: RecordId, record: RecordReplace) -> repository.Row:
    with http_errors():
        return repository.replace_record(record_id, record.model_dump())


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
    responses={404: RECORD_NOT_FOUND},
)
def delete_record(record_id: RecordId) -> None:
    with http_errors():
        repository.delete_record(record_id)
