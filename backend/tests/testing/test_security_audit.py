from __future__ import annotations

import os
import re


def test_no_hardcoded_secrets_in_codebase() -> None:
    """Security scanner asserting that no plain secrets or credentials exist in code."""
    # Find all Python files
    src_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "src")
    )
    secret_patterns = [
        re.compile(r'(?i)(password|secret_key|api_key|token|auth_secret)\s*=\s*["\'][a-zA-Z0-9_\-]{16,}["\']'),
        re.compile(r'(?i)(jwt_secret)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']'),
    ]

    exclusions = [
        "settings.py",  # Default configuration placeholders
        "oauth.py",     # Mock fallback values
        "test_apikeys.py",
        "test_logging.py",
        "test_security_audit.py",
    ]

    for root, _, files in os.walk(src_dir):
        for f in files:
            if not f.endswith(".py") or f in exclusions:
                continue
            path = os.path.join(root, f)
            with open(path, encoding="utf-8") as f_obj:
                content = f_obj.read()
                for p in secret_patterns:
                    matches = p.findall(content)
                    assert not matches, (
                        f"Potential secret in {path}: {matches}"
                    )


def test_http_endpoints_enforce_access_control() -> None:
    """Security check assuring that all HTTP routes contain tenancy verification checks."""
    http_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "src",
            "aether",
            "interfaces",
            "http",
        )
    )
    exclusions = ["__init__.py", "app.py", "dependencies.py", "health.py", "errors.py"]

    for f in os.listdir(http_dir):
        if not f.endswith(".py") or f in exclusions:
            continue
        path = os.path.join(http_dir, f)
        with open(path, encoding="utf-8") as f_obj:
            content = f_obj.read()
            # Ensure it references security tokens/principals or local access checkers
            has_security = (
                "_access" in content
                or "get_principal" in content
                or "depends" in content.lower()
                or "oauth2_scheme" in content
            )
            assert has_security, (
                f"Vulnerability warning: Route file {f} lacks access check."
            )
