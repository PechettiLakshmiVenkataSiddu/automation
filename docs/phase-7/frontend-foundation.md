# Phase 7 — Frontend Foundation

## Delivered scope

The web application is a strict TypeScript Next.js application using the App Router, Tailwind CSS, React Query for server-state infrastructure, and Zustand for local session state. It provides an accessible sign-in experience that begins the OAuth flow through the Phase 6 API.

## Structure

```text
apps/web/
├── app/                 Routes, layout, global styles, and providers
├── components/          Reusable UI and feature components
├── lib/                 Environment and API helpers
├── stores/              Client-local state
└── public/              Static assets
```

## Run

```text
pnpm install
pnpm --filter @aether/web dev
```

Set `NEXT_PUBLIC_API_BASE_URL` in `apps/web/.env.local` to the Phase 6 API origin, for example `http://localhost:8000`.

## Test and validate

```text
pnpm --filter @aether/web lint
pnpm --filter @aether/web typecheck
pnpm --filter @aether/web test
```
