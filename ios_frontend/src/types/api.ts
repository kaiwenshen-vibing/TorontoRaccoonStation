export type PaginatedResponse<T> = {
  items: T[];
  limit: number;
  offset: number;
  total: number;
};

export type StoreItem = {
  store_id: number;
  name: string;
  pic_storage_key: string | null;
};

export type RoomItem = {
  store_room_id: number;
  store_id: number;
  name: string;
  is_active: boolean;
  pic_storage_key: string | null;
};

export type SlotItem = {
  slot_id: number;
  store_id: number;
  start_at: string;
};

export type BookingItem = {
  booking_id: number;
  store_id: number;
  script_id: number | null;
  booking_status_id: number;
  target_month: string | null;
  start_at: string | null;
  end_at: string | null;
  duration_override_minutes: number | null;
  client_ids: number[];
  has_conflict: boolean;
  conflict_count: number;
  conflict_booking_ids: number[];
};

export type BookingFilters = {
  bookingStatusId?: number;
  targetMonth?: string;
  hasConflict?: boolean;
};

export type SessionState = {
  actorId: string;
  allowedStoreIds: number[];
  selectedStoreId: number | null;
};
