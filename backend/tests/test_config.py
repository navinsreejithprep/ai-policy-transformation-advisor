from app.config import Settings


def test_allowed_origins_list_splits_and_trims():
    settings = Settings(allowed_origins="http://localhost:3000, https://my-app.vercel.app ,")
    assert settings.allowed_origins_list() == ["http://localhost:3000", "https://my-app.vercel.app"]


def test_allowed_origins_list_defaults_to_localhost():
    settings = Settings(allowed_origins="http://localhost:3000")
    assert settings.allowed_origins_list() == ["http://localhost:3000"]
