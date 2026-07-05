from app.core.config import Settings


def test_default_cors_origins() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.cors_allow_origins == ["http://localhost:5173"]


def test_cors_origins_parsed_from_csv_env_var(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://localhost:3000")

    settings = Settings()

    assert settings.cors_allow_origins == ["http://localhost:5173", "http://localhost:3000"]


def test_cors_origins_single_value_env_var(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://example.com")

    settings = Settings()

    assert settings.cors_allow_origins == ["http://example.com"]
