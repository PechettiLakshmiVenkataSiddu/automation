"""Whisper transcription and Piper synthesis inside the executor boundary."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from voice_access import validate_audio_payload, validate_synthesis_text


def transcribe_audio(content: bytes, audio_format: str) -> str:
    workspace = Path(tempfile.mkdtemp(prefix="aether-voice-"))
    try:
        input_path = workspace / f"input.{audio_format}"
        input_path.write_bytes(content)
        transcript = _run_whisper(input_path)
        if not transcript.strip():
            raise ValueError("Transcription produced no text")
        return transcript.strip()
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def synthesize_text(text: str) -> bytes:
    workspace = Path(tempfile.mkdtemp(prefix="aether-voice-"))
    try:
        cleaned = validate_synthesis_text(text)
        output_path = workspace / "output.wav"
        _run_piper(cleaned, output_path)
        return output_path.read_bytes()
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def _run_whisper(audio_path: Path) -> str:
    model = os.environ.get("VOICE_WHISPER_MODEL", "tiny")
    try:
        from faster_whisper import WhisperModel  # type: ignore[import-not-found]

        whisper = WhisperModel(model, device="cpu", compute_type="int8")
        segments, _info = whisper.transcribe(str(audio_path), beam_size=1)
        return " ".join(segment.text.strip() for segment in segments)
    except ImportError:
        return _fallback_transcribe(audio_path)


def _fallback_transcribe(audio_path: Path) -> str:
    command = [
        "whisper",
        str(audio_path),
        "--model",
        "tiny",
        "--output_format",
        "txt",
        "--fp16",
        "False",
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    _ = result
    transcript_path = audio_path.with_suffix(".txt")
    if transcript_path.exists():
        return transcript_path.read_text(encoding="utf-8")
    raise RuntimeError("Whisper transcription failed")


def _run_piper(text: str, output_path: Path) -> None:
    voice_model = os.environ.get("VOICE_PIPER_VOICE", "")
    piper_bin = os.environ.get("PIPER_BINARY", "piper")
    if voice_model and shutil.which(piper_bin):
        subprocess.run(
            [piper_bin, "--model", voice_model, "--output_file", str(output_path)],
            input=text,
            text=True,
            check=True,
            capture_output=True,
            timeout=60,
        )
        return
    try:
        from piper import PiperVoice  # type: ignore[import-not-found]

        model_path = voice_model or os.environ.get("VOICE_PIPER_MODEL_PATH", "")
        if not model_path:
            raise ValueError("Piper voice model is not configured")
        voice = PiperVoice.load(model_path)
        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize(text, wav_file)
        return
    except Exception as error:
        raise RuntimeError("Piper synthesis is unavailable") from error


def execute_transcribe(payload: dict[str, Any]) -> tuple[str, bool]:
    content = validate_audio_payload(payload)
    audio_format = str(payload["format"])
    transcript = transcribe_audio(content, audio_format)
    return transcript, True


def execute_synthesize(payload: dict[str, Any]) -> tuple[bytes, bool]:
    text = validate_synthesis_text(str(payload["text"]))
    audio = synthesize_text(text)
    return audio, True
