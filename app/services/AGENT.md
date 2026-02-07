# AGENT.md — `app/services`

## Purpose

This folder owns business logic and orchestration.
FastAPI routes should call these classes; services should not depend on HTTP layer details.

## Hard Rules

- Keep business rules in service classes, not in routes.
- Accept plain Python/Pydantic inputs, return schema-friendly outputs.
- Do not use FastAPI request/response objects in services.
- Keep writes transactional; `confirm` must be atomic.
- Use explicit, deterministic validation errors for business rule failures.

## Core Domain Rules To Preserve

- Booking flow: `incomplete -> confirm -> scheduled`.
- `incomplete` requires:
  - `target_month`
  - at least 1 linked client (`booking_client`)
- Confirm requires:
  - `script_id` present
  - strict bijection between non-DM characters and clients
  - slot upsert by `(store_id, start_at)`
  - room assignment (prefer non-conflict, allow conflict)
- Response conflict payload should include:
  - `has_conflict`
  - `conflict_count`
  - `conflict_booking_ids`

## Service Boundaries

- `BookingService`: booking lifecycle and confirm orchestration.
- `SlotService`: slot CRUD/upsert helpers.
- `RoomService`: room CRUD and room selection hooks.
- `CharacterClientMatchService`: non-DM character/client matching.
- `CharacterDmMatchService`: DM assignment and extra DM slots.
- `ConflictService`: overlap/conflict reads.

## Editing Guidance

- Prefer adding methods to existing service classes before creating new ones.
- Keep method signatures stable and explicit.
- When schema changes affect logic, update root `AGENT.md` and migration docs.

