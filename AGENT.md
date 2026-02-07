# AGENT.md — Store Scheduler MVP Ground Truth

## 0. Summary

This file is the current source of truth for MVP decisions.
If any older doc conflicts with this file, this file wins.

- Product focus: store-side scheduler first
- Booking flow: `incomplete -> confirm -> scheduled`
- API stack: FastAPI + Pydantic
- API style: thin routes, business logic in injected service classes
- Time format: ISO 8601 with timezone offset

## 1. MVP Scope

### 1.1 In Scope
- Store manages rooms and slots
- Store creates and manages bookings
- Booking statuses: `incomplete`, `scheduled`, `cancelled`, `completed`
- Script-based duration with per-booking override
- Character-to-client and character-to-DM assignment
- Soft room-time conflict policy (allow + surface warning)

### 1.2 Out of Scope
- Client self-booking
- Payment/deposit
- Legacy carpool/session/signup/user_lockin flow
- Redis抢位/high-concurrency reservation workflow
- Client DM lock rule (future: max 2 DM-character locks per booking)

## 2. Core Business Rules

### 2.1 Slot and Confirmation
- `slot` is reusable and keyed by `(store_id, start_at)`.
- `scheduled` booking must link to slot + room + exact `start_at`.
- Confirm action upserts/finds slot by `(store_id, start_at)`.

### 2.2 Incomplete vs Scheduled
- `incomplete`:
  - uses `target_month`
  - may have `script_id = NULL`
  - must have at least 1 client on the booking
- `scheduled`/`completed`:
  - must have `script_id`
  - must have `start_at/end_at/slot_id/store_room_id`

### 2.3 Character Assignment Rules
- `script_character` is live source (no snapshot).
- `is_dm = false` means client character.
- `is_dm = true` means DM character.
- Confirm precondition:
  - all non-DM characters have exactly 1 client match
  - all booking clients are used exactly once in non-DM matching
  - strict bijection between non-DM characters and booking clients

### 2.4 Room Conflict Policy
- Overlap is allowed (never blocked by DB).
- Confirm should prefer non-overlap room first.
- If no clean room exists, auto-assign and return conflict details.

### 2.5 Permissions
- Current writer role: store staff only.
- All store routes require strict store ownership authorization.

## 3. Data Model Ground Truth (Target)

## 3.1 `store`
- `store_id`, `name`, timestamps
- No `timezone` column

## 3.2 `store_room`
- `store_room_id`, `store_id`, `name`, `is_active`, timestamps
- Unique: `(store_id, name)`
- Operational expectation: each store keeps at least one active room

## 3.3 `slot`
- `slot_id`, `store_id`, `start_at`, timestamps
- Unique: `(store_id, start_at)`
- Reusable across multiple bookings

## 3.4 `script` (global)
- `script_id`, `name`, `estimated_minutes`, timestamps

## 3.5 `store_script`
- `store_id`, `script_id`, `is_active`, timestamps
- One script can map to many stores; each store controls `is_active`

## 3.6 `script_character`
- `character_id`, `script_id`, `character_name`, `is_dm`, `is_active`, timestamps
- Unique: `(script_id, character_name)`

## 3.7 `dm` and `dm_store_membership`
- `dm`: global DM profile (`dm_id`, `display_name`, `is_active`, timestamps)
- `dm_store_membership`: (`dm_id`, `store_id`) membership table
- Same DM can belong to multiple stores

## 3.8 `client` (global)
- `client_id`, `display_name`, `phone`, timestamps

## 3.9 `booking_status` (lookup)
- `booking_status_id`, `booking_status_name`
- Canonical ids:
  - `1 = incomplete`
  - `2 = scheduled`
  - `3 = cancelled`
  - `4 = completed`

## 3.10 `booking`
- `booking_id`, `store_id`, `script_id` (nullable only for incomplete)
- `slot_id`, `store_room_id`
- `booking_status_id`
- `target_month`, `start_at`, `end_at`
- `duration_override_minutes`
- timestamps
- FK rule: `(store_id, script_id)` should map to active `store_script` when script is set

## 3.11 `booking_client`
- Join table for many clients per booking
- Fields: `booking_client_id`, `booking_id`, `client_id`, timestamps
- Unique: `(booking_id, client_id)`

## 3.12 `character_client_match`
- Fields: `character_client_match_id`, `booking_id`, `character_id`, `client_id`, timestamps
- For non-DM characters (`is_dm = false`)
- Target uniqueness:
  - one client per character in a booking
  - one character per client in a booking

## 3.13 `character_dm_match`
- Fields: `character_dm_match_id`, `booking_id`, `character_id` nullable, `dm_id`, timestamps
- `character_id` set for DM-character assignment
- `character_id = NULL` for extra/free DM slot

## 4. Constraints and Validation Rules

### 4.1 Booking Shape
- `incomplete (1)`:
  - `target_month` required
  - `start_at/end_at/slot_id/store_room_id` null
- `scheduled/completed (2,4)`:
  - `script_id/start_at/end_at/slot_id/store_room_id` required
  - `target_month` null
- `cancelled (3)`:
  - may represent cancelled-incomplete or cancelled-scheduled

### 4.2 Confirm Preconditions (Hard Validation)
- booking is `incomplete`
- `script_id` is present and active for store
- booking has at least 1 client
- strict bijection passes for non-DM characters and clients

### 4.3 Trigger Rules
- `set_booking_end_at()` computes `end_at` from `start_at` and effective duration
- DM assignment must pass store membership rule via `dm_store_membership`

## 5. API Ground Truth

### 5.1 API Style
- Prefix: `/api/v1`
- Store-scoped routes: `/api/v1/stores/{store_id}/...`
- Explicit path `store_id` plus strict authz check
- Plain JSON responses (no envelope)
- List pagination: offset pagination (`limit`, `offset`)

### 5.2 Booking APIs (Core)
- `POST /api/v1/stores/{store_id}/bookings/incomplete`
- `GET /api/v1/stores/{store_id}/bookings`
- `GET /api/v1/stores/{store_id}/bookings/{booking_id}`
- `PATCH /api/v1/stores/{store_id}/bookings/{booking_id}`
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/confirm`
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/cancel`
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/complete`

### 5.3 Client and Match APIs
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/clients`
- `DELETE /api/v1/stores/{store_id}/bookings/{booking_id}/clients/{client_id}`
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/character-client-matches`
- `PATCH /api/v1/stores/{store_id}/bookings/{booking_id}/character-client-matches/{match_id}`
- `DELETE /api/v1/stores/{store_id}/bookings/{booking_id}/character-client-matches/{match_id}`
- `POST /api/v1/stores/{store_id}/bookings/{booking_id}/character-dm-matches`
- `PATCH /api/v1/stores/{store_id}/bookings/{booking_id}/character-dm-matches/{match_id}`
- `DELETE /api/v1/stores/{store_id}/bookings/{booking_id}/character-dm-matches/{match_id}`

### 5.4 Slot/Room/Script APIs
- `GET/POST/PATCH/DELETE /api/v1/stores/{store_id}/slots...`
- `GET/POST/PATCH /api/v1/stores/{store_id}/rooms...`
- `GET /api/v1/stores/{store_id}/scripts` (respect `store_script.is_active`)

## 6. Service Architecture Ground Truth

- Keep FastAPI routes thin.
- Business logic must live in injected service classes for testability.
- Recommended service split:
  - `BookingService`
  - `SlotService`
  - `RoomService`
  - `CharacterClientMatchService`
  - `CharacterDmMatchService`
  - `ConflictService`
- Writes are synchronous and transactional.
- `confirm` is atomic.

## 7. Conflict Response Contract

Booking responses should include:
- `has_conflict: bool`
- `conflict_count: int`
- `conflict_booking_ids: list[int]`

## 8. International Text Input (Chinese Support)

All user-facing text fields must support Chinese input.

- Schema should use `TEXT`/Unicode-capable types.
- No ASCII-only regex/check constraints on user text fields.
- PostgreSQL encoding must be UTF-8:
  - `SHOW server_encoding;` = `UTF8`
  - `SHOW client_encoding;` = `UTF8`

## 9. Migration Policy

- Current repo has a squashed baseline migration: `0001_store_scheduler_core`.
- Current forward migration for match model: `0002_booking_match_model`.
- As new ground-truth model evolves (e.g. `booking_client`, `character_client_match`, `character_dm_match`), add forward migrations or resquash before production lock.
- Keep schema and AGENT ground truth aligned at all times.
