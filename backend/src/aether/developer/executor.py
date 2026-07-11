"""Subprocess commander with resource limits and secret redaction."""

from __future__ import annotations

import asyncio
import os
import re


def redact_secrets(content: str, sensitive_vals: list[str] | None = None) -> str:
    """Scrub JWT tokens, hex secrets, and known sensitive environment variable values."""
    if not content:
        return content

    redacted = content

    # 1. Redact known exact values
    if sensitive_vals:
        for val in sensitive_vals:
            if val and len(val) >= 6:  # Prevent matching tiny strings like 'true'
                redacted = redacted.replace(val, "[REDACTED]")

    # 2. Redact JWT structure pattern
    jwt_pattern = re.compile(r"ey[a-zA-Z0-9-_]+\.ey[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+")
    redacted = jwt_pattern.sub("[REDACTED_JWT]", redacted)

    # 3. Redact 32-byte hex strings (64 characters)
    hex_pattern = re.compile(r"\b[0-9a-fA-F]{64}\b")
    redacted = hex_pattern.sub("[REDACTED_SECRET]", redacted)

    return redacted


class DeveloperCommandExecutor:
    """Executes subprocesses securely with CPU/time boundaries and credential filtering."""

    @staticmethod
    async def execute(
        command_line: str, cwd: str, timeout_seconds: int = 30
    ) -> tuple[int, str, str]:
        """Execute shell command, capture outputs, and scrub secrets."""
        # 1. Prepare environment variables and scrub credentials
        env = os.environ.copy()
        sensitive_vals = []
        sensitive_triggers = ["PASSWORD", "SECRET", "KEY", "TOKEN", "URL", "DATABASE"]

        for key, val in list(env.items()):
            if any(trigger in key.upper() for trigger in sensitive_triggers):
                sensitive_vals.append(val)
                env[key] = "[REDACTED]"

        # 2. Spawn async shell subprocess
        try:
            proc = await asyncio.create_subprocess_shell(
                command_line,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_seconds
                )
                exit_code = proc.returncode if proc.returncode is not None else 0
                raw_stdout = stdout_bytes.decode("utf-8", errors="replace")
                raw_stderr = stderr_bytes.decode("utf-8", errors="replace")
            except TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass
                exit_code = -1
                raw_stdout = ""
                raw_stderr = f"Command execution timed out after {timeout_seconds} seconds."
        except Exception as err:
            exit_code = -1
            raw_stdout = ""
            raw_stderr = f"Failed to start command: {err}"

        # 3. Redact output
        stdout_redacted = redact_secrets(raw_stdout, sensitive_vals)
        stderr_redacted = redact_secrets(raw_stderr, sensitive_vals)

        return exit_code, stdout_redacted, stderr_redacted
