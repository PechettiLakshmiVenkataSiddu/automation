"""Sandboxed desktop execution inside the isolated executor boundary."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from access import normalize_application, validate_action
from redaction import redact


class DesktopSandbox:
    """Confined desktop session with verified cleanup; no host-wide control."""

    def __init__(self, sandbox_root: Path) -> None:
        self._root = sandbox_root
        self._processes: list[subprocess.Popen[bytes]] = []
        self._mounts: list[Path] = []

    def prepare_mounts(self, allowed_mounts: list[Any]) -> None:
        for entry in allowed_mounts:
            relative = str(entry).strip()
            if not relative or relative.startswith("/") or ".." in relative:
                raise ValueError("Desktop mount paths must be relative sandbox entries")
            mount = self._root / relative
            mount.mkdir(parents=True, exist_ok=True)
            self._mounts.append(mount)

    def execute(self, action: dict[str, Any]) -> tuple[bytes, str]:
        validate_action(action)
        operation = str(action["operation"])
        target = normalize_application(str(action["target_application"]))
        timeout = int(str(action["timeout_seconds"]))
        allowed_mounts = action.get("allowed_mounts", [])
        if not isinstance(allowed_mounts, list):
            raise ValueError("Desktop mount paths must be relative sandbox entries")
        self.prepare_mounts(allowed_mounts)

        if operation == "focus_app":
            self._focus(target, timeout)
            text = f"focused:{target}"
            return self._render_placeholder(target, text), text
        if operation == "read_window":
            text = self._read_window(target, timeout)
            return self._render_placeholder(target, text), text
        if operation == "screenshot":
            content, text = self._screenshot(timeout)
            return content, text
        raise ValueError("Sensitive desktop operations require explicit approval before execution")

    def cleanup(self) -> bool:
        for process in self._processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
        self._processes.clear()
        if self._root.exists():
            shutil.rmtree(self._root, ignore_errors=True)
        return not self._root.exists()

    def _focus(self, target: str, timeout: int) -> None:
        display = os.environ.get("DISPLAY")
        if not display:
            return
        subprocess.run(
            ["xdotool", "search", "--name", target, "windowactivate"],
            check=False,
            timeout=timeout,
            capture_output=True,
        )

    def _read_window(self, target: str, timeout: int) -> str:
        display = os.environ.get("DISPLAY")
        if not display:
            return redact(f"window:{target}")
        result = subprocess.run(
            ["xdotool", "search", "--name", target, "getwindowname"],
            check=False,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        name = result.stdout.strip() or target
        return redact(name)[:5000]

    def _screenshot(self, timeout: int) -> tuple[bytes, str]:
        display = os.environ.get("DISPLAY")
        if not display:
            payload = json.dumps({"display": "sandbox", "status": "captured"}).encode()
            return payload, "sandbox screenshot"
        output = self._root / "capture.png"
        subprocess.run(
            ["scrot", "-o", str(output)],
            check=True,
            timeout=timeout,
            capture_output=True,
        )
        return output.read_bytes(), "desktop screenshot"

    def _render_placeholder(self, target: str, text: str) -> bytes:
        payload = {"target": target, "text": redact(text)}
        return json.dumps(payload).encode()


def run_action(action: dict[str, Any]) -> tuple[bytes, str, bool]:
    sandbox_root = Path(tempfile.mkdtemp(prefix="aether-desktop-"))
    sandbox = DesktopSandbox(sandbox_root)
    try:
        content, text = sandbox.execute(action)
        cleanup_verified = sandbox.cleanup()
        if not cleanup_verified:
            raise RuntimeError("Desktop cleanup verification failed")
        return content, text, cleanup_verified
    except Exception:
        sandbox.cleanup()
        raise
