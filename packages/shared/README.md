# @resumeforge/shared

Shared TypeScript types and utilities for the ResumeForge monorepo.

## Purpose

This package will contain **auto-generated TypeScript types** derived from the
backend's OpenAPI schema, ensuring complete type-safety between the FastAPI
backend and the Next.js frontend without manual duplication.

## Phase 0 Status

This package is a **placeholder** for Phase 0. Real content will be added in
**Phase 2+** when the backend API surface has stabilised enough to generate
types from.

## Planned Contents (Phase 2+)

| Module | Description |
|---|---|
| `src/types/api.ts` | Auto-generated types from OpenAPI schema (`openapi-typescript`) |
| `src/types/resume.ts` | Resume domain types shared between frontend and backend |
| `src/types/user.ts` | User and auth types |
| `src/utils/validation.ts` | Shared Zod validation schemas |
| `src/index.ts` | Barrel export |

## Type Generation

Once the backend API is stable, types will be generated automatically:

```bash
# From repo root
npx openapi-typescript http://localhost:8000/openapi.json \
  -o packages/shared/src/types/api.ts
```

This is wired into the frontend build via the `@resumeforge/shared` workspace
dependency in `apps/frontend/package.json`.

## Usage (Phase 2+)

```typescript
import type { ResumeSchema, AnalysisResult } from "@resumeforge/shared";
```
