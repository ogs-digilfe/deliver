from collections.abc import Iterator
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient
import pytest

import deliver.main as main


@pytest.fixture
def admin_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    admin = main.UserInDb(
        username="test-admin",
        hashed_password="dummy-hash",
        salt="dummy-salt",
        role="admin",
        status="active",
        registered="2026-01-01",
        updated="2026-01-01",
    )
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    main.app.dependency_overrides[main.get_admin_user] = lambda: admin

    with TestClient(main.app) as client:
        yield client

    main.app.dependency_overrides.clear()


def create_dummy_zip() -> bytes:
    archive = BytesIO()
    with ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("portfolio.csv", "symbol,quantity\nTEST,10\n")
    return archive.getvalue()


def test_upload_portfolio_saves_zip_file(
    admin_client: TestClient,
    tmp_path: Path,
) -> None:
    zip_data = create_dummy_zip()

    response = admin_client.post(
        "/upload-portfolio",
        files={"file": ("portfolio.zip", zip_data, "application/zip")},
    )

    assert response.status_code == 200
    assert response.json()["upload_file"] == "portfolio.zip"
    assert (tmp_path / "portfolio" / "portfolio.zip").read_bytes() == zip_data
