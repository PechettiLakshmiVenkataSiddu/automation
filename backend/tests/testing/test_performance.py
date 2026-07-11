from __future__ import annotations

import time

from aether.analytics.policy import AnalyticsPolicyEvaluator


def test_metadata_scrubbing_performance() -> None:
    """Ensures scrubbing metadata dictionary is computationally cheap and low-latency."""
    evaluator = AnalyticsPolicyEvaluator()

    large_meta = {
        f"key_{i}": f"value_{i}" if i % 10 != 0 else "secret_token_abc"
        for i in range(100)
    }

    start = time.perf_counter()
    # Execute 1,000 times
    for _ in range(1000):
        evaluator.scrub_event_metadata(large_meta)
    duration = time.perf_counter() - start

    # Average execution time should be well under 1ms (1000 runs under 500ms)
    assert duration < 0.500, f"Performance budget exceeded: took {duration:.3f}s for 1000 scrubs"
