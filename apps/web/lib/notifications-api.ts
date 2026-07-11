import { api } from '@/lib/chat-api';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  level: 'info' | 'warning' | 'error';
  status: 'unread' | 'read';
  sent_channels: string[];
  created_at: string;
}

export interface NotificationPreferences {
  channels: Array<'in_app' | 'email' | 'push'>;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  unsubscribed: boolean;
}

export function getNotifications(token: string, organization_id: string): Promise<NotificationItem[]> {
  return api(`/v1/notifications?organization_id=${organization_id}`, token);
}

export function markRead(
  token: string,
  organization_id: string,
  notification_id: string,
): Promise<{ status: string }> {
  return api(`/v1/notifications/${notification_id}/read?organization_id=${organization_id}`, token, {
    method: 'POST',
  });
}

export function getPreferences(token: string, organization_id: string): Promise<NotificationPreferences> {
  return api(`/v1/notifications/preferences?organization_id=${organization_id}`, token);
}

export function updatePreferences(
  token: string,
  organization_id: string,
  channels: Array<'in_app' | 'email' | 'push'>,
  quiet_hours_start: string | null,
  quiet_hours_end: string | null,
  unsubscribed: boolean,
): Promise<{ status: string }> {
  return api('/v1/notifications/preferences', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      channels,
      quiet_hours_start,
      quiet_hours_end,
      unsubscribed,
    }),
  });
}

export function dispatchNotification(
  token: string,
  organization_id: string,
  title: string,
  message: string,
  level: 'info' | 'warning' | 'error' = 'info',
): Promise<{ notification_id: string | null }> {
  return api('/v1/notifications/dispatch', token, {
    method: 'POST',
    body: JSON.stringify({
      organization_id,
      title,
      message,
      level,
    }),
  });
}
