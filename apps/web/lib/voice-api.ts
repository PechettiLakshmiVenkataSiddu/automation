import { api } from '@/lib/chat-api';

export function setVoiceConsent(
  token: string,
  organization_id: string,
  capture_enabled: boolean,
  retention_enabled: boolean,
): Promise<{ capture_enabled: boolean; retention_enabled: boolean }> {
  return api('/v1/voice/consent', token, {
    method: 'PUT',
    body: JSON.stringify({ organization_id, capture_enabled, retention_enabled }),
  });
}

export function getVoiceConsent(
  token: string,
  organization_id: string,
): Promise<{ capture_enabled: boolean; retention_enabled: boolean }> {
  return api(`/v1/voice/consent?organization_id=${organization_id}`, token);
}

export function createVoiceSession(
  token: string,
  organization_id: string,
  idempotency_key: string,
  conversation_id?: string,
): Promise<{ id: string; status: string }> {
  return api('/v1/voice/sessions', token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, conversation_id, idempotency_key }),
  });
}

export function uploadVoiceAudio(
  token: string,
  session_id: string,
  organization_id: string,
  format: string,
  content_base64: string,
  duration_seconds: number,
): Promise<{ session_id: string; status: string }> {
  return api(`/v1/voice/sessions/${session_id}/audio`, token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      format,
      content_base64,
      duration_seconds,
    }),
  });
}

export function parseVoiceCommand(
  token: string,
  session_id: string,
  organization_id: string,
  transcript: string,
): Promise<{
  confirmation_id: string;
  intent_type: string;
  transcript: string;
  requires_confirmation: boolean;
}> {
  return api(`/v1/voice/sessions/${session_id}/commands`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, session_id, transcript }),
  });
}

export function decideVoiceConfirmation(
  token: string,
  confirmation_id: string,
  organization_id: string,
  confirmed: boolean,
): Promise<{ voice_session_id: string; decision: string }> {
  return api(`/v1/voice/confirmations/${confirmation_id}/decision`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, confirmed }),
  });
}

export function getVoiceSession(
  token: string,
  session_id: string,
  organization_id: string,
): Promise<{ id: string; status: string; retention_mode: string; transcript: string | null; expires_at: string }> {
  return api(`/v1/voice/sessions/${session_id}?organization_id=${organization_id}`, token);
}

