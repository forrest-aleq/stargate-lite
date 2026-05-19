import importlib


def test_init_posthog_sets_capture_api_key(monkeypatch) -> None:
    monkeypatch.setenv("POSTHOG_API_KEY", "phc_test_key")

    import app.posthog_client as posthog_client

    module = importlib.reload(posthog_client)
    module._initialized = False
    module.posthog.api_key = None
    module.posthog.project_api_key = None

    assert module.init_posthog() is True
    assert module.posthog.api_key == "phc_test_key"
    assert module.posthog.project_api_key == "phc_test_key"


def test_track_skips_when_posthog_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)

    import app.posthog_client as posthog_client

    module = importlib.reload(posthog_client)
    module._initialized = False

    def _boom(*args, **kwargs) -> None:
        raise AssertionError("capture should not run when analytics are disabled")

    monkeypatch.setattr(module.posthog, "capture", _boom)

    module.track(
        event="capability_called",
        user_id="user_123",
        org_id="org_123",
        properties={"capability_key": "fci.revenue"},
    )
