import { api } from '@/lib/chat-api';

export interface CalendarEvent {
  id: string;
  google_event_id: string;
  summary: string;
  description: string | null;
  start_time: string;
  end_time: string;
  attendees: Array<{ email: string; name?: string }>;
  status: 'confirmed' | 'tentative' | 'cancelled';
}

export interface CalendarProposal {
  id: string;
  summary: string;
  description: string | null;
  start_time: string;
  end_time: string;
  attendees: Array<{ email: string; name?: string }>;
  status: 'pending' | 'approved' | 'rejected';
  conflict_detected: boolean;
  decision_reason: string | null;
  created_at: string;
}

export function createConnection(
  token: string,
  organization_id: string,
  access_token: string,
  refresh_token: string,
  scopes: string[] = [],
  permitted_calendars: string[] = [],
  expires_in_seconds = 3600,
): Promise<{ connection_id: string }> {
  return api('/v1/calendar/connections', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      access_token,
      refresh_token,
      scopes,
      permitted_calendars,
      expires_in_seconds,
    }),
  });
}

export function revokeConnection(
  token: string,
  organization_id: string,
): Promise<{ status: string }> {
  return api(`/v1/calendar/connections?organization_id=${organization_id}`, token, {
    method: 'DELETE',
  });
}

export function getEvents(
  token: string,
  organization_id: string,
  start_time: string,
  end_time: string,
): Promise<CalendarEvent[]> {
  return api(
    `/v1/calendar/events?organization_id=${organization_id}&start_time=${encodeURIComponent(
      start_time
    )}&end_time=${encodeURIComponent(end_time)}`,
    token
  );
}

export function proposeEvent(
  token: string,
  organization_id: string,
  summary: string,
  description: string | null,
  start_time: string,
  end_time: string,
  attendees: Array<{ email: string; name?: string }> = [],
): Promise<{ id: string; type: 'event' | 'proposal'; status: string; conflict_detected: boolean }> {
  return api('/v1/calendar/proposals', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      summary,
      description,
      start_time,
      end_time,
      attendees,
    }),
  });
}

export function getProposals(
  token: string,
  organization_id: string,
): Promise<CalendarProposal[]> {
  return api(`/v1/calendar/proposals?organization_id=${organization_id}`, token);
}

export function decideProposal(
  token: string,
  organization_id: string,
  proposal_id: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return api(`/v1/calendar/proposals/${proposal_id}/approve`, token, {
    method: 'POST',
    body: JSON.stringify({ organization_id, approved, reason }),
  });
}
