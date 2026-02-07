# Store Scheduler API Design (MVP)

## Scope
- Store-first scheduling API
- FastAPI + Pydantic
- Thin route handlers
- Service-class business logic (dependency injected)

## API Conventions
- Base path: `/api/v1`
- Store scope in path: `/stores/{store_id}/...`
- Authz rule: request actor must be allowed for `store_id`
- Response style: plain JSON
- List pagination: `limit`, `offset`
- Datetime fields: ISO 8601 with timezone offset

## Booking Flow
1. Create booking as `incomplete`
2. Add clients to booking (`booking_client`)
3. Set `script_id` (nullable before confirm)
4. Build matches:
   - `character_client_match` for non-DM characters
   - `character_dm_match` for DM characters (or free DM with null character)
5. Confirm booking:
   - validate preconditions
   - upsert/find slot by `(store_id, start_at)`
   - assign room (prefer no conflict, allow overlap)
   - transition to `scheduled`

## Confirm Preconditions
- Booking status is `incomplete`
- `script_id` is set
- At least one client linked to booking
- Strict bijection for non-DM characters and booking clients:
  - every non-DM character has exactly one client
  - every booking client maps to exactly one non-DM character

## Conflict Contract
- Responses include:
  - `has_conflict`
  - `conflict_count`
  - `conflict_booking_ids`

## Database Evolution
- Baseline: `0001_store_scheduler_core`
- Forward migration: `0002_booking_match_model`
  - add `booking_client`
  - add `character_client_match`
  - add `character_dm_match`
  - migrate old `booking.client_id` and `booking_dm_assignment`
  - update booking state constraint to allow nullable `script_id` for `incomplete`

## Route Inventory
- Bookings:
  - `POST /stores/{store_id}/bookings/incomplete`
  - `GET /stores/{store_id}/bookings`
  - `GET /stores/{store_id}/bookings/{booking_id}`
  - `PATCH /stores/{store_id}/bookings/{booking_id}`
  - `POST /stores/{store_id}/bookings/{booking_id}/confirm`
  - `POST /stores/{store_id}/bookings/{booking_id}/cancel`
  - `POST /stores/{store_id}/bookings/{booking_id}/complete`
- Booking clients:
  - `POST /stores/{store_id}/bookings/{booking_id}/clients`
  - `DELETE /stores/{store_id}/bookings/{booking_id}/clients/{client_id}`
- Character matches:
  - `POST/PATCH/DELETE /stores/{store_id}/bookings/{booking_id}/character-client-matches...`
  - `POST/PATCH/DELETE /stores/{store_id}/bookings/{booking_id}/character-dm-matches...`
- Slots:
  - `GET/POST/PATCH/DELETE /stores/{store_id}/slots...`
- Rooms:
  - `GET/POST/PATCH /stores/{store_id}/rooms...`
- Scripts:
  - `GET /stores/{store_id}/scripts`

