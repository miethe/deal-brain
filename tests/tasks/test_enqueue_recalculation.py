from typing import Any
import sys
import types


class _DummyTask:
    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self._func(*args, **kwargs)


class _StubCelery:
    def __init__(self, *args, **kwargs):
        pass

    def config_from_object(self, *args, **kwargs):
        return None

    def task(self, *decorator_args, **decorator_kwargs):
        def _decorator(func):
            return _DummyTask(func)

        return _decorator


celery_stub = types.ModuleType("celery")
celery_stub.Celery = _StubCelery
sys.modules.setdefault("celery", celery_stub)

from apps.api.dealbrain_api.tasks import valuation  # noqa: E402


def test_enqueue_listing_recalculation_accepts_reason(monkeypatch):
    """Ensure enqueue supports optional reason argument without Celery errors."""

    captured: dict[str, Any] = {}

    def _fake_task(**kwargs):
        captured.update(kwargs)
        return {"processed": 0, "succeeded": 0, "failed": 0}

    monkeypatch.setattr(valuation, "recalculate_listings_task", _fake_task)

    valuation.enqueue_listing_recalculation(
        ruleset_id=42,
        listing_ids=[1, 2],
        reason="rule_updated",
        use_celery=False,
    )

    assert captured["ruleset_id"] == 42
    assert captured["listing_ids"] == [1, 2]
    assert captured["reason"] == "rule_updated"
