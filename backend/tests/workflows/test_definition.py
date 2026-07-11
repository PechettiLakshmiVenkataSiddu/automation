import pytest

from aether.workflows.definition import InvalidWorkflowDefinition, validate_definition


def test_rejects_cycles_without_a_loop() -> None:
    with pytest.raises(InvalidWorkflowDefinition, match="Cycles require"):
        validate_definition(
            {
                "nodes": [{"id": "start", "type": "trigger"}, {"id": "send", "type": "action"}],
                "edges": [
                    {"source": "start", "target": "send"},
                    {"source": "send", "target": "start"},
                ],
            }
        )


def test_accepts_bounded_explicit_loop() -> None:
    definition = {
        "nodes": [
            {"id": "start", "type": "trigger"},
            {"id": "loop", "type": "loop", "config": {"max_iterations": 3}},
        ],
        "edges": [{"source": "start", "target": "loop"}, {"source": "loop", "target": "start"}],
    }
    assert len(validate_definition(definition).definition_hash) == 64
