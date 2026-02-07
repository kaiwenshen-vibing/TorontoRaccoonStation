# AGENT.md — `app/api/v1`

## Purpose

This folder contains thin HTTP route handlers for `/api/v1`.

## Hard Rules

- Keep routes thin:
  - parse path/query/body
  - call service methods
  - return response models
- Do not put business logic in route files.
- Use dependency injection from `app/core/dependencies.py`.
- Enforce store-scope authorization through the shared dependency chain.

## API Conventions

- Base prefix is `/api/v1`.
- Store-scoped routes must use `/stores/{store_id}/...`.
- Responses are plain JSON (no global envelope).
- List endpoints use offset pagination:
  - `limit` (default 20, max 100)
  - `offset` (default 0)
- Datetime fields are ISO 8601 with timezone offset (`AwareDatetime` in schemas).

## Status Codes

- `201` for creates.
- `204` for delete-without-body.
- `400/403/404/409/422` from validation and business checks.
- `501` allowed for scaffolded but unimplemented service calls.

## Editing Guidance

- If adding an endpoint:
  1. Add/extend request/response schema in `app/schemas/`.
  2. Add service method signature in `app/services/`.
  3. Keep handler body minimal (no data access SQL in route).
- Keep names aligned with root `AGENT.md` ground truth.

