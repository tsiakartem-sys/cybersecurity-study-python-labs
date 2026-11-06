"""Маршрути API та спільне перетворення помилок шару даних на HTTP-коди."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import HTTPException, status

from labs.lab03.repository import ConflictError, NotFoundError
from labs.lab03.schemas import ErrorResponse


def error_response(description: str) -> dict[str, Any]:
    """Опис можливої помилки для Swagger UI."""
    return {"model": ErrorResponse, "description": description}


@contextmanager
def http_errors() -> Iterator[None]:
    """Перетворити NotFoundError на 404, а ConflictError на 409."""
    try:
        yield
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
