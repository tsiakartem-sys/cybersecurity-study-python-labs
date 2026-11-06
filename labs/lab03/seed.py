"""Початкове заповнення бази навчальними даними з data/seed.json.

Запуск з кореня репозиторію:
    python -m labs.lab03.seed
"""

import sqlite3
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from labs.lab03 import repository
from labs.lab03.database import initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


class SeedCategory(CategoryCreate):
    """Категорія початкового набору з явно заданим id."""

    id: int = Field(gt=0)


class SeedData(BaseModel):
    """Структура seed.json: три категорії та вісім записів."""

    model_config = ConfigDict(extra="forbid", strict=True)

    categories: list[SeedCategory] = Field(min_length=3, max_length=3)
    records: list[RecordCreate] = Field(min_length=8, max_length=8)


def load_seed(path: Path) -> SeedData:
    """Прочитати JSON і перевірити його через Pydantic."""
    return SeedData.model_validate_json(path.read_text(encoding="utf-8"))


def main() -> int:
    """Створити таблиці та заповнити порожню базу початковими даними."""
    initialize_database()

    try:
        data = load_seed(SEED_PATH)
    except OSError as exc:
        print(f"Не вдалося прочитати {SEED_PATH.name}: {exc.strerror}")
        return 1
    except ValidationError as exc:
        print(f"Початкові дані в {SEED_PATH.name} некоректні, базу не змінено:")
        print(exc)
        return 1

    categories = [category.model_dump() for category in data.categories]
    records = [record.model_dump() for record in data.records]
    try:
        seeded = repository.seed_database(categories, records)
    except sqlite3.IntegrityError as exc:
        print(f"Дані порушують обмеження бази ({exc}); жоден запис не збережено.")
        return 1

    if not seeded:
        print("База вже містить дані: повторне заповнення пропущено, дані не змінено.")
        return 0
    print(f"Базу заповнено: {len(categories)} категорії, {len(records)} записів.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
