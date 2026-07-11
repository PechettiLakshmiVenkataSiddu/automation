'use client';

import { FormEvent, useRef, useState } from 'react';

import { getOrganizations, refreshAccessToken } from '@/lib/chat-api';
import {
  createVoiceSession,
  decideVoiceConfirmation,
  getVoiceConsent,
  parseVoiceCommand,
  setVoiceConsent,
  uploadVoiceAudio,
} from '@/lib/voice-api';

type PendingConfirmation = {
  confirmation_id: string;
  intent_type: string;
  transcript: string;
};

export function VoiceWorkspace() {
  const [captureEnabled, setCaptureEnabled] = useState(false);
  const [retentionEnabled, setRetentionEnabled] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState('');
  const [pending, setPending] = useState<PendingConfirmation | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function ensureOrganization(token: string): Promise<string> {
    const organizations = await getOrganizations(token);
    if (!organizations[0]) throw new Error('No active workspace is available.');
    return organizations[0].id;
  }

  async function toggleConsent(enabled: boolean) {
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const consent = await setVoiceConsent(
        token,
        organizationId,
        enabled,
        enabled ? retentionEnabled : false,
      );
      setCaptureEnabled(consent.capture_enabled);
      setRetentionEnabled(consent.retention_enabled);
      setStatus(enabled ? 'Voice capture consent granted.' : 'Voice capture consent withdrawn.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Consent update failed.');
    } finally {
      setBusy(false);
    }
  }

  async function startSession() {
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const consent = await getVoiceConsent(token, organizationId);
      if (!consent.capture_enabled) throw new Error('Enable voice capture consent first.');
      const session = await createVoiceSession(token, organizationId, crypto.randomUUID());
      setSessionId(session.id);
      setStatus(`Voice session ${session.id} is active.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Session creation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function submitTranscript(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sessionId || !transcript.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const command = await parseVoiceCommand(token, sessionId, organizationId, transcript.trim());
      setPending({
        confirmation_id: command.confirmation_id,
        intent_type: command.intent_type,
        transcript: command.transcript,
      });
      setStatus('Voice command parsed. Confirm before execution.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Command parsing failed.');
    } finally {
      setBusy(false);
    }
  }

  async function decide(confirmed: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const result = await decideVoiceConfirmation(
        token,
        pending.confirmation_id,
        organizationId,
        confirmed,
      );
      setStatus(`Voice command ${result.decision}.`);
      setPending(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Confirmation failed.');
    } finally {
      setBusy(false);
    }
  }

  async function uploadAudio(file: File) {
    if (!sessionId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const token = await refreshAccessToken();
      const organizationId = await ensureOrganization(token);
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = '';
      for (const byte of bytes) binary += String.fromCharCode(byte);
      const content_base64 = btoa(binary);
      const extension = file.name.split('.').pop() ?? 'webm';
      await uploadVoiceAudio(token, sessionId, organizationId, extension, content_base64, 30);
      setStatus('Audio uploaded for transcription.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Audio upload failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col p-6">
      <header>
        <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">AETHER</p>
        <h1 className="mt-2 text-3xl font-semibold">Voice Assistant</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Audio is ephemeral by default unless retention consent is enabled.
        </p>
      </header>

      <section className="mt-8 space-y-4" aria-live="polite">
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => toggleConsent(true)}
            className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
          >
            Enable voice consent
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => toggleConsent(false)}
            className="rounded-md border px-4 py-2 text-sm"
          >
            Withdraw consent
          </button>
          <button
            type="button"
            disabled={busy || !captureEnabled}
            onClick={startSession}
            className="rounded-md border px-4 py-2 text-sm"
          >
            Start session
          </button>
          <button
            type="button"
            disabled={busy || !sessionId}
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md border px-4 py-2 text-sm"
          >
            Upload audio
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="audio/*"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void uploadAudio(file);
            }}
          />
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={retentionEnabled}
            disabled={!captureEnabled || busy}
            onChange={(event) => setRetentionEnabled(event.target.checked)}
          />
          Retain voice artifacts when consent is enabled
        </label>

        <form onSubmit={submitTranscript} className="flex flex-col gap-3">
          <label htmlFor="voice-transcript" className="text-sm font-medium">
            Transcript
          </label>
          <textarea
            id="voice-transcript"
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={4}
            className="rounded-md border px-3 py-2"
            placeholder="Speak or paste a command transcript"
          />
          <button
            type="submit"
            disabled={busy || !sessionId}
            className="self-start rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
          >
            Parse command
          </button>
        </form>

        {pending ? (
          <article className="rounded-md border p-4">
            <p className="text-sm font-medium">Confirm voice command</p>
            <p className="mt-2 text-sm">{pending.transcript}</p>
            <p className="mt-1 text-xs text-[var(--muted)]">Intent: {pending.intent_type}</p>
            <div className="mt-4 flex gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={() => decide(true)}
                className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm text-white"
              >
                Confirm
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => decide(false)}
                className="rounded-md border px-4 py-2 text-sm"
              >
                Reject
              </button>
            </div>
          </article>
        ) : null}

        {status ? <p className="text-sm text-green-700">{status}</p> : null}
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
      </section>
    </main>
  );
}
