"""Isolated desktop executor HTTP service; never runs inside API or worker processes."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

from access import validate_action
from executor import run_action
from grants import verify_grant
from redaction import redact

GRANT_SECRET = os.environ.get("DESKTOP_GRANT_SECRET", "").encode()
EXECUTOR_SECRET = os.environ.get("DESKTOP_EXECUTOR_SECRET", "")
CONTROL_PLANE_URL = os.environ.get("CONTROL_PLANE_URL", "")

if len(GRANT_SECRET) < 32:
    raise RuntimeError("DESKTOP_GRANT_SECRET must be at least 32 bytes.")
if len(EXECUTOR_SECRET) < 32 or not CONTROL_PLANE_URL:
    raise RuntimeError("Executor control-plane configuration is required.")


def _post(path: str, payload: dict[str, object]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{CONTROL_PLANE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Desktop-Executor-Secret": EXECUTOR_SECRET,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return cast(dict[str, Any], json.loads(response.read().decode()))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)

    def do_POST(self) -> None:
        if self.path != "/execute":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode())
            grant = str(payload["grant"])
            action = payload["action"]
            claims_org, claims_task = verify_grant(GRANT_SECRET, grant)
            if str(claims_org) != str(action["organization_id"]) or str(claims_task) != str(
                action["task_id"]
            ):
                raise ValueError("Grant scope mismatch")
            validate_action(action)
            content, text, cleanup_verified = run_action(action)
            artifact_type = (
                "screenshot" if str(action["operation"]) == "screenshot" else "window_dump"
            )
            artifact = _post(
                "/v1/desktop-tasks/internal/artifacts",
                {
                    "organization_id": str(action["organization_id"]),
                    "task_id": str(action["task_id"]),
                    "artifact_type": artifact_type,
                    "content_base64": base64.b64encode(content).decode(),
                },
            )
            _post(
                "/v1/desktop-tasks/internal/status",
                {
                    "organization_id": str(action["organization_id"]),
                    "task_id": str(action["task_id"]),
                    "succeeded": True,
                    "cleanup_verified": cleanup_verified,
                },
            )
            self._json(
                200,
                {
                    "task_id": str(action["task_id"]),
                    "artifact": artifact,
                    "text": redact(text),
                    "cleanup_verified": cleanup_verified,
                },
            )
        except (ValueError, urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as error:
            self._json(422, {"error": "desktop_task_rejected", "detail": redact(str(error))})

    def _json(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8081), Handler).serve_forever()
