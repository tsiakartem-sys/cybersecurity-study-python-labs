"""Шар доступу до даних: параметризовані SQL-запити до categories і records.

Модуль не залежить від FastAPI: помилки повідомляються винятками
NotFoundError і ConflictError, а в HTTP-коди їх перетворює шар API.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from typing import Any

from labs.lab03.database import get_connection

Row = dict[str, Any]

RECORD_SELECT = """
    SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name,
           r.value, r.status
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""

RECORD_INSERT = """
    INSERT INTO records (code, title, category_id, value, status)
    VALUES (:code, :title, :category_id, :value, :status)
"""


class NotFoundError(Exception):
    """Запис або категорію не знайдено."""


class ConflictError(Exception):
    """Дублікат унікального значення або категорія містить записи."""


@contextmanager
def _transaction() -> Iterator[sqlite3.Connection]:
    """Відкрити з'єднання, виконати операції в одній транзакції й закрити його.

    `with connection` підтверджує зміни за успіху або скасовує їх за винятку,
    а `closing` гарантує закриття з'єднання.
    """
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            yield connection


# --- Допоміжні перевірки в межах відкритого з'єднання ---


def _ensure_category_exists(connection: sqlite3.Connection, category_id: int) -> None:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError(f"Категорію з id={category_id} не знайдено")


def _ensure_code_is_free(
    connection: sqlite3.Connection, code: str, exclude_id: int | None = None
) -> None:
    row = connection.execute(
        "SELECT id FROM records WHERE code = ?", (code,)
    ).fetchone()
    if row is not None and row["id"] != exclude_id:
        raise ConflictError(f"Запис з code '{code}' вже існує")


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> Row:
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Запис з id={record_id} не знайдено")
    return dict(row)


def _insert_record(connection: sqlite3.Connection, record: Row) -> int:
    _ensure_category_exists(connection, record["category_id"])
    _ensure_code_is_free(connection, record["code"])
    return connection.execute(RECORD_INSERT, record).lastrowid


# --- Категорії ---


def list_categories() -> list[Row]:
    """Повернути всі категорії за зростанням id."""
    with _transaction() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def create_category(name: str) -> Row:
    """Створити категорію; дублікат назви — ConflictError."""
    with _transaction() as connection:
        exists = connection.execute(
            "SELECT 1 FROM categories WHERE name = ?", (name,)
        ).fetchone()
        if exists is not None:
            raise ConflictError(f"Категорія '{name}' вже існує")
        cursor = connection.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return {"id": cursor.lastrowid, "name": name}


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію; категорію із записами видаляти не можна."""
    with _transaction() as connection:
        _ensure_category_exists(connection, category_id)
        has_records = connection.execute(
            "SELECT 1 FROM records WHERE category_id = ? LIMIT 1", (category_id,)
        ).fetchone()
        if has_records is not None:
            raise ConflictError(f"Категорія з id={category_id} містить записи")
        connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# --- Записи ---


def get_record(record_id: int) -> Row:
    """Повернути запис за id разом із назвою категорії."""
    with _transaction() as connection:
        return _fetch_record(connection, record_id)


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Row]:
    """Повернути сторінку записів; фільтри об'єднуються через AND."""
    # SQL-фрагменти лише з наперед визначених рядків, значення — окремо
    conditions: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        # instr шукає буквальний підрядок з урахуванням регістру
        conditions.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with _transaction() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def create_record(record: Row) -> Row:
    """Додати запис і повернути його разом з id та category_name."""
    with _transaction() as connection:
        record_id = _insert_record(connection, record)
        return _fetch_record(connection, record_id)


def replace_record(record_id: int, record: Row) -> Row:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    with _transaction() as connection:
        _fetch_record(connection, record_id)
        _ensure_category_exists(connection, record["category_id"])
        _ensure_code_is_free(connection, record["code"], exclude_id=record_id)
        connection.execute(
            """
            UPDATE records
            SET code = :code, title = :title, category_id = :category_id,
                value = :value, status = :status
            WHERE id = :id
            """,
            {**record, "id": record_id},
        )
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис за id."""
    with _transaction() as connection:
        _fetch_record(connection, record_id)
        connection.execute("DELETE FROM records WHERE id = ?", (record_id,))


def create_records_bulk(records: list[Row]) -> list[Row]:
    """Додати пакет записів в одній транзакції: усі або жодного.

    Дублікат code (у базі чи всередині пакета) або неіснуюча категорія
    перериває вставлення, і `with connection` скасовує всі зміни пакета.
    """
    with _transaction() as connection:
        record_ids = [_insert_record(connection, record) for record in records]
        return [_fetch_record(connection, record_id) for record_id in record_ids]


# --- Початкове заповнення ---


def seed_database(categories: list[Row], records: list[Row]) -> bool:
    """Заповнити порожню базу в одній транзакції.

    Повертає False без змін, якщо база вже містить дані. Порушення
    обмежень піднімає sqlite3.IntegrityError, і весь пакет скасовується.
    """
    with _transaction() as connection:
        not_empty = connection.execute(
            "SELECT EXISTS (SELECT 1 FROM categories) OR EXISTS (SELECT 1 FROM records)"
        ).fetchone()[0]
        if not_empty:
            return False
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (:id, :name)", categories
        )
        connection.executemany(RECORD_INSERT, records)
    return True
