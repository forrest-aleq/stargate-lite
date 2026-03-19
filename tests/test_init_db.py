import os

from app import database


def test_init_db_skip_alembic_verifies_minimum_schema(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_create_all(*, bind, tables, checkfirst):  # type: ignore[no-untyped-def]
        calls["bind"] = bind
        calls["tables"] = tables
        calls["checkfirst"] = checkfirst

    monkeypatch.setenv("SKIP_ALEMBIC", "true")
    monkeypatch.setattr(database.Base.metadata, "create_all", fake_create_all)

    database.init_db()

    assert calls["bind"] is database.engine
    assert calls["tables"] == [database.CredentialStore.__table__]
    assert calls["checkfirst"] is True

    monkeypatch.delenv("SKIP_ALEMBIC", raising=False)
