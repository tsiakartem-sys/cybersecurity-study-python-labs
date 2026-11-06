"""Лабораторна робота №3: FastAPI-застосунок обліку часу відновлення сервісів.

Запуск з кореня репозиторію:
    python -m labs.lab03.seed
    uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from labs.lab03.config import APP_DESCRIPTION, APP_TITLE
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from labs.lab03.schemas import PingResponse, StudentRead
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску, не змінюючи наявних даних."""
    initialize_database()
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Повернути 422 без поля input: значення на кшталт inf не серіалізуються в JSON."""
    errors = [
        {key: value for key, value in error.items() if key != "input"}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(errors)},
    )


@app.exception_handler(sqlite3.Error)
async def database_error_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
    """Записати технічні деталі в журнал, а клієнту повернути загальне повідомлення."""
    logger.error(
        "Помилка бази даних: %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутрішня помилка сервера, спробуйте пізніше"},
    )


@app.get("/ping", tags=["service"], summary="Перевірка доступності API")
def ping() -> PingResponse:
    return PingResponse(status="ok")


@app.get("/student", tags=["service"], summary="Дані студента")
def student() -> StudentRead:
    return StudentRead(
        student_name=STUDENT_NAME,
        group_name=GROUP_NAME,
        variant_number=VARIANT_NUMBER,
    )
