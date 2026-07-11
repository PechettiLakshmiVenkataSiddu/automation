from aether.interfaces.http.health import liveness


async def test_liveness_does_not_require_infrastructure() -> None:
    assert await liveness() == {"status": "ok"}
