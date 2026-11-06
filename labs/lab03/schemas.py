"""Pydantic-моделі запитів і відповідей API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03.config import UNIT, VALUE_MIN

Status = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Тіло запиту для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    name: str = Field(min_length=2, max_length=40, examples=["backup_service"])


class CategoryRead(CategoryCreate):
    """Категорія, яку повертає API."""

    id: int


class RecordCreate(BaseModel):
    """Тіло запиту для створення запису; id задає база."""

    # strict=True: рядок "12" чи true не перетворюються на число мовчки
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    code: str = Field(min_length=3, max_length=40, examples=["V08-09"])
    title: str = Field(
        min_length=3, max_length=120, examples=["Вимірювання відновлення 09"]
    )
    category_id: int = Field(gt=0, examples=[1])
    value: float = Field(
        ge=VALUE_MIN,
        allow_inf_nan=False,
        description=f"Час відновлення, {UNIT}",
        examples=[45.0],
    )
    status: Status = Field(examples=["new"])


class RecordReplace(RecordCreate):
    """Тіло PUT-запиту: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис разом з id та назвою категорії."""

    id: int
    category_name: str


class StudentRead(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int


class PingResponse(BaseModel):
    """Відповідь перевірки доступності."""

    status: Literal["ok"]


class ErrorResponse(BaseModel):
    """Опис помилки для документації 404 та 409."""

    detail: str
