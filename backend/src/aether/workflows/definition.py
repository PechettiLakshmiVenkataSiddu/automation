"""Validation for versioned workflow graphs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from aether.shared.errors import AetherError


class InvalidWorkflowDefinition(AetherError):
    """A draft graph cannot be made into an immutable workflow version."""


_NODE_TYPES = {"trigger", "action", "condition", "approval", "loop"}


@dataclass(frozen=True, slots=True)
class ValidatedDefinition:
    value: dict[str, object]
    definition_hash: str


def validate_definition(value: dict[str, object]) -> ValidatedDefinition:
    nodes = value.get("nodes")
    edges = value.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise InvalidWorkflowDefinition("Definition requires nodes and edges arrays")
    ids: set[str] = set()
    node_types: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise InvalidWorkflowDefinition("Every node must be an object")
        node_id, node_type = node.get("id"), node.get("type")
        if not isinstance(node_id, str) or not node_id or node_id in ids:
            raise InvalidWorkflowDefinition("Node ids must be unique non-empty strings")
        if node_type not in _NODE_TYPES:
            raise InvalidWorkflowDefinition("Unsupported workflow node type")
        if node_type == "loop":
            config = node.get("config")
            if not isinstance(config, dict) or not isinstance(config.get("max_iterations"), int):
                raise InvalidWorkflowDefinition("Loop nodes require an integer max_iterations")
            if not 1 <= config["max_iterations"] <= 100:
                raise InvalidWorkflowDefinition("Loop max_iterations must be between 1 and 100")
        ids.add(node_id)
        node_types[node_id] = node_type
    if not ids or sum(kind == "trigger" for kind in node_types.values()) != 1:
        raise InvalidWorkflowDefinition("A workflow requires exactly one trigger")
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in ids}
    for edge in edges:
        if not isinstance(edge, dict):
            raise InvalidWorkflowDefinition("Every edge must be an object")
        source, target = edge.get("source"), edge.get("target")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in ids
            or target not in ids
        ):
            raise InvalidWorkflowDefinition("Edges must reference existing nodes")
        if source == target:
            raise InvalidWorkflowDefinition("A node cannot point to itself")
        adjacency[source].append(target)
    _validate_cycles(adjacency, node_types)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return ValidatedDefinition(value, hashlib.sha256(canonical.encode()).hexdigest())


def _validate_cycles(adjacency: dict[str, list[str]], node_types: dict[str, str]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: list[str]) -> None:
        if node_id in visiting:
            cycle = path[path.index(node_id) :]
            if not any(node_types[item] == "loop" for item in cycle):
                raise InvalidWorkflowDefinition("Cycles require an explicit loop node")
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for target in adjacency[node_id]:
            visit(target, [*path, target])
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in adjacency:
        visit(node_id, [node_id])
