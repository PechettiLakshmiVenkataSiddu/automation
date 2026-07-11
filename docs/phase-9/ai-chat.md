# Phase 9 — AI Chat

## Delivered scope

AI Chat provides organization-scoped conversation creation and message exchange. Messages are persisted in PostgreSQL and sent through a provider-neutral chat gateway. The initial concrete adapter targets an OpenAI-compatible Chat Completions endpoint, allowing OpenAI and compatible hosted or self-hosted deployments through configuration.

## Security boundary

Every route validates the signed access token, non-revoked session, and active organization membership. Provider credentials remain server-only. The browser receives the assistant response but never an AI provider secret.

## Configuration

Set `AI_CHAT_BASE_URL`, `AI_CHAT_API_KEY`, and `AI_CHAT_MODEL`. The base URL must point to an OpenAI-compatible API root, for example `https://api.openai.com/v1`.
