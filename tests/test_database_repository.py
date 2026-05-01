import pytest

from app.repositories.database_repository import DatabaseRepository


def test_sanitize_query_adds_limit_when_missing() -> None:
    repository = DatabaseRepository()

    sanitized = repository._sanitize_select_query(
        "SELECT title FROM videos WHERE topic LIKE '%calculo%'",
        limit=5,
    )

    assert sanitized.endswith("LIMIT 5")


def test_sanitize_query_blocks_non_allowed_tables() -> None:
    repository = DatabaseRepository()

    with pytest.raises(ValueError):
        repository._sanitize_select_query("SELECT * FROM metrics LIMIT 3", limit=3)
