# AGENT.md — `app/schemas`

## Purpose

Pydantic models that define API request/response contracts.

## Hard Rules

- Schemas are API contracts; change carefully.
- Keep field names stable unless versioning/migration is planned.
- Use strict typing and validators for domain rules.
- Use `AwareDatetime` for datetime fields exposed by API.
- Keep date-only fields (`target_month`) as `date`.

## Validation Guidance

- Validate month fields as first day of month when needed.
- For patch payloads, enforce "at least one field provided" via model validators.
- Keep limits on list/input sizes where relevant.

## Contract Conventions

- List responses should include:
  - `items`
  - `limit`
  - `offset`
  - `total`
- Booking response should include conflict fields:
  - `has_conflict`
  - `conflict_count`
  - `conflict_booking_ids`

## Editing Guidance

- When adding fields, update:
  1. corresponding service method outputs
  2. route response_model annotations
  3. any design docs/root `AGENT.md` if behavior changes

