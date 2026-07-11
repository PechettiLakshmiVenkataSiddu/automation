export type OAuthProvider = 'google' | 'github';

function apiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!url) throw new Error('NEXT_PUBLIC_API_BASE_URL is not configured.');
  return url.replace(/\/$/, '');
}

export function beginOAuthLogin(provider: OAuthProvider, redirectUri: string): string {
  const query = new URLSearchParams({ redirect_uri: redirectUri });
  return `${apiBaseUrl()}/v1/auth/${provider}/login?${query.toString()}`;
}
