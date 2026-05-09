import pytest

from app.repositories.database_repository import DatabaseRepository


class FakeCursor:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.executed_queries: list[str] = []
        self.closed = False

    def execute(self, query: str, _params: tuple[object, ...]) -> None:
        self.executed_queries.append(query)

    def fetchall(self) -> list[dict]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows
        self.cursor_calls = 0
        self.closed = False

    def cursor(self, dictionary: bool = False) -> FakeCursor:
        assert dictionary is True
        self.cursor_calls += 1
        return FakeCursor(self.rows)

    def close(self) -> None:
        self.closed = True


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


def test_execute_resource_queries_reuses_single_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = DatabaseRepository()
    fake_connection = FakeConnection(rows=[{"title": "Calculo"}])
    get_connection_calls = 0

    def fake_get_connection() -> FakeConnection:
        nonlocal get_connection_calls
        get_connection_calls += 1
        return fake_connection

    monkeypatch.setattr(repository, "get_connection", fake_get_connection)

    results = repository.execute_resource_queries(
        {
            "videos_query": "SELECT title FROM videos LIMIT 1",
            "literature_query": "SELECT title FROM literature LIMIT 1",
            "disciplines_query": "SELECT name FROM disciplines LIMIT 1",
        },
        limit=3,
    )

    assert get_connection_calls == 1
    assert fake_connection.cursor_calls == 3
    assert fake_connection.closed is True
    assert results["videos_query"] == [{"title": "Calculo"}]
