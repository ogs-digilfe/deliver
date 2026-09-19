from fastapi.testclient import TestClient

from deliver import main


def active_user() -> main.UserInDb:
    return main.UserInDb(
        username="test-user", hashed_password="unused", salt="unused",
        role="user", status="active", registered="2026-01-01", updated="2026-01-01",
    )


def request_download(tmp_path, monkeypatch, filename: str):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(main, "DATA_DIR", data_dir)
    main.app.dependency_overrides[main.get_current_active_user] = active_user
    try:
        return TestClient(main.app).get(
            "/download-portfolio", params={"filename": filename}
        )
    finally:
        main.app.dependency_overrides.clear()


def test_download_portfolio_returns_selected_zip_and_moves_it(tmp_path, monkeypatch) -> None:
    portfolio_dir = tmp_path / "data" / "portfolio"
    portfolio_dir.mkdir(parents=True)
    selected = portfolio_dir / "selected.zip"
    remaining = portfolio_dir / "remaining.zip"
    selected.write_bytes(b"selected zip")
    remaining.write_bytes(b"remaining zip")

    response = request_download(tmp_path, monkeypatch, "selected.zip")

    assert response.status_code == 200
    assert response.content == b"selected zip"
    assert response.headers["content-type"] == "application/zip"
    assert not selected.exists()
    assert (portfolio_dir / "downloaded" / "selected.zip").read_bytes() == b"selected zip"
    assert remaining.read_bytes() == b"remaining zip"


def test_download_portfolio_returns_404_when_file_does_not_exist(tmp_path, monkeypatch) -> None:
    response = request_download(tmp_path, monkeypatch, "missing.zip")
    assert response.status_code == 404
    assert response.json() == {"detail": "Portfolio file not found"}


def test_download_portfolio_rejects_invalid_filename(tmp_path, monkeypatch) -> None:
    for filename in ("../secret.zip", "/tmp/secret.zip", "portfolio.txt"):
        response = request_download(tmp_path, monkeypatch, filename)
        assert response.status_code == 400
        assert response.json() == {"detail": "Invalid filename"}
