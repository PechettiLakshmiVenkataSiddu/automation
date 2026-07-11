"""Isolated voice executor HTTP service; never runs inside API or worker processes."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

from voice_access import validate_synthesis_text
from voice_engine import execute_synthesize, execute_transcribe
from voice_grants import verify_grant

GRANT_SECRET = os.environ.get("VOICE_GRANT_SECRET", "").encode()
EXECUTOR_SECRET = os.environ.get("VOICE_EXECUTOR_SECRET", "")
CONTROL_PLANE_URL = os.environ.get("CONTROL_PLANE_URL", "")

if len(GRANT_SECRET) < 32:
    raise RuntimeError("VOICE_GRANT_SECRET must be at least 32 bytes.")
if len(EXECUTOR_SECRET) < 32 or not CONTROL_PLANE_URL:
    raise RuntimeError("Executor control-plane configuration is required.")


def _post(path: str, payload: dict[str, object]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{CONTROL_PLANE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Voice-Executor-Secret": EXECUTOR_SECRET,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return cast(dict[str, Any], json.loads(response.read().decode()))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        _ = (format, args)

    def do_POST(self) -> None:
        if self.path not in {"/transcribe", "/synthesize"}:
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode())
            grant = str(payload["grant"])
            action = payload["action"]
            claims_org, claims_session = verify_grant(GRANT_SECRET, grant)
            if str(claims_org) != str(action["organization_id"]) or str(claims_session) != str(
                action["session_id"]
            ):
                raise ValueError("Grant scope mismatch")
            if self.path == "/transcribe":
                transcript, cleanup_verified = execute_transcribe(action)
                result = _post(
                    "/v1/voice/internal/transcript",
                    {
                        "organization_id": str(action["organization_id"]),
                        "session_id": str(action["session_id"]),
                        "transcript": transcript,
                    },
                )
                self._json(
                    200,
                    {
                        "session_id": str(action["session_id"]),
                        "transcript": transcript,
                        "confirmation": result,
                        "cleanup_verified": cleanup_verified,
                    },
                )
                return
            validate_synthesis_text(str(action["text"]))
            audio, cleanup_verified = execute_synthesize(action)
            artifact = _post(
                "/v1/voice/internal/artifacts",
                {
                    "organization_id": str(action["organization_id"]),
                    "session_id": str(action["session_id"]),
                    "artifact_type": "audio_output",
                    "content_base64": base64.b64encode(audio).decode(),
                },
            )
            _post(
                "/v1/voice/internal/status",
                {
                    "organization_id": str(action["organization_id"]),
                    "session_id": str(action["session_id"]),
                    "succeeded": True,
                    "cleanup_verified": cleanup_verified,
                },
            )
            self._json(
                200,
                {
                    "session_id": str(action["session_id"]),
                    "artifact": artifact,
                    "audio_base64": base64.b64encode(audio).decode(),
                    "cleanup_verified": cleanup_verified,
                },
            )
        except (ValueError, urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as error:
            self._json(422, {"error": "voice_task_rejected", "detail": str(error)})

    def _json(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8082), Handler).serve_forever()
