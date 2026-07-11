import { describe, expect, it } from 'vitest';

import { beginOAuthLogin } from './auth-api';

describe('beginOAuthLogin', () => {
  it('creates an encoded login URL', () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000/';
    expect(beginOAuthLogin('google', 'http://localhost:3000/auth/callback')).toBe(
      'http://localhost:8000/v1/auth/google/login?redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback',
    );
  });
});
