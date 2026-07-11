from __future__ import annotations

import os

import pytest


def test_migrations_are_sequentially_numbered() -> None:
    """Verifies that database schema migration SQL files follow a strict numbering order."""
    schema_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "database",
            "schema",
        )
    )

    if not os.path.exists(schema_dir):
        pytest.skip("database/schema directory does not exist")

    sql_files = sorted([f for f in os.listdir(schema_dir) if f.endswith(".sql")])
    assert sql_files, "No migration sql files found."

    # Validate sequence starts at 0001 and has no gaps
    for idx, filename in enumerate(sql_files, start=1):
        prefix = f"{idx:04d}_"
        assert filename.startswith(prefix), (
            f"Migration sequence gap: expected {prefix} in name, got {filename}"
        )


def test_migrations_basic_syntax() -> None:
    """Checks that migration sql scripts contain basic correct SQL structure."""
    schema_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "database",
            "schema",
        )
    )

    if not os.path.exists(schema_dir):
        pytest.skip("database/schema directory does not exist")

    for f in os.listdir(schema_dir):
        if not f.endswith(".sql"):
            continue
        path = os.path.join(schema_dir, f)
        with open(path, encoding="utf-8") as f_obj:
            content = f_obj.read()
            # Assert semicolons or create statements on non-comment lines
            clean = "\n".join(
                line for line in content.splitlines() if not line.strip().startswith("--")
            )
            if clean.strip():
                assert ";" in clean, f"Migration {f} might be missing closing statement semicolons."
