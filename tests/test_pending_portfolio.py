from fastapi.testclient import TestClient

from deliver import main


def active_user() -> main.UserInDb:
    return main.UserInDb(
        username="test-user",
        hashed_password="unused",
        salt="unused",
        role="user",
        status="active",
        registered="2026-01-01",
        updated="2026-01-01",
    )


def request_pending_files(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path / "data")
    main.app.dependency_overrides[main.get_current_active_user] = active_user
    try:
        return TestClient(main.app).get("/portfolio/pending")
    finally:
        main.app.dependency_overrides.clear()


def test_get_pending_portfolio_file_names(tmp_path, monkeypatch) -> None:
    portfolio_dir = tmp_path / "data" / "portfolio"
    downloaded_dir = portfolio_dir / "downloaded"
    downloaded_dir.mkdir(parents=True)
    (portfolio_dir / "second.zip").write_bytes(b"second")
    (portfolio_dir / "first.ZIP").write_bytes(b"first")
    (portfolio_dir / "ignored.txt").write_text("ignored", encoding="utf-8")
    (downloaded_dir / "downloaded.zip").write_bytes(b"downloaded")

    response = request_pending_files(tmp_path, monkeypatch)

    assert response.status_code == 200
    assert response.json() == {"files": ["first.ZIP", "second.zip"]}


def test_get_pending_portfolio_file_names_returns_empty_list(
    tmp_path, monkeypatch
) -> None:
    response = request_pending_files(tmp_path, monkeypatch)
    assert response.status_code == 200
    assert response.json() == {"files": []}
