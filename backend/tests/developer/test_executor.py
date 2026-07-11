from __future__ import annotations

import pytest

from aether.developer.executor import DeveloperCommandExecutor, redact_secrets


@pytest.mark.asyncio
async def test_executor_command_execution() -> None:
    # Run a basic safe command
    exit_code, stdout, stderr = await DeveloperCommandExecutor.execute("echo Hello", cwd=".")
    assert exit_code == 0
    assert "Hello" in stdout
    assert stderr == ""


@pytest.mark.asyncio
async def test_executor_timeout_limits() -> None:
    # Run a command that sleeps to trigger timeout (e.g. sleep 5s with a 1s timeout limit)
    # Using python sleep command to be platform-independent
    cmd = 'python -c "import time; time.sleep(5)"'
    exit_code, stdout, stderr = await DeveloperCommandExecutor.execute(
        cmd, cwd=".", timeout_seconds=1
    )
    assert exit_code == -1
    assert stdout == ""
    assert "timed out" in stderr


def test_secret_redactor_scrubbing() -> None:
    # 1. Exact value scrubbing
    res = redact_secrets("my value contains super_secret", ["super_secret"])
    assert res == "my value contains [REDACTED]"

    # 2. JWT token regex matching
    fake_jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    assert redact_secrets(f"auth {fake_jwt} headers") == "auth [REDACTED_JWT] headers"

    # 3. 32-byte hex key regex matching
    fake_hex = "a" * 64
    assert redact_secrets(f"secret key {fake_hex}") == "secret key [REDACTED_SECRET]"
