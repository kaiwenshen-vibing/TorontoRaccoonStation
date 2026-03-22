import { schedulerApi } from "@/lib/api";
import type { BookingFilters } from "@/types/api";
import type { SessionState } from "@/types/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "@/providers/SessionProvider";

function useOptionalSession() {
  const { session } = useSession();
  return session;
}

function assertSession(session: SessionState | null) {
  if (!session) {
    throw new Error("Session is required");
  }
  return session;
}

export function useStoresQuery() {
  const session = useOptionalSession();
  return useQuery({
    queryKey: ["stores", session?.actorId ?? "anonymous", session?.allowedStoreIds.join(",") ?? ""],
    queryFn: () => schedulerApi.listStores(assertSession(session)),
    enabled: !!session
  });
}

export function useBookingsQuery(storeId: number, filters: BookingFilters) {
  const session = useOptionalSession();
  return useQuery({
    queryKey: ["bookings", storeId, filters, session?.actorId ?? "anonymous", session?.allowedStoreIds.join(",") ?? ""],
    queryFn: () => schedulerApi.listBookings(storeId, filters, assertSession(session)),
    enabled: !!session
  });
}

export function useBookingQuery(storeId: number, bookingId: number) {
  const session = useOptionalSession();
  return useQuery({
    queryKey: ["booking", storeId, bookingId, session?.actorId ?? "anonymous"],
    queryFn: () => schedulerApi.getBooking(storeId, bookingId, assertSession(session)),
    enabled: !!session
  });
}

export function useRoomsQuery(storeId: number) {
  const session = useOptionalSession();
  return useQuery({
    queryKey: ["rooms", storeId, session?.actorId ?? "anonymous"],
    queryFn: () => schedulerApi.listRooms(storeId, assertSession(session)),
    enabled: !!session
  });
}

export function useSlotsQuery(storeId: number) {
  const session = useOptionalSession();
  return useQuery({
    queryKey: ["slots", storeId, session?.actorId ?? "anonymous"],
    queryFn: () => schedulerApi.listSlots(storeId, assertSession(session)),
    enabled: !!session
  });
}

export function useRoomMutations(storeId: number) {
  const session = useOptionalSession();
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["rooms", storeId] });

  return {
    createRoom: useMutation({
      mutationFn: (payload: { name: string }) => schedulerApi.createRoom(storeId, payload, assertSession(session)),
      onSuccess: invalidate
    }),
    updateRoom: useMutation({
      mutationFn: (payload: { roomId: number; name?: string; is_active?: boolean }) =>
        schedulerApi.updateRoom(storeId, payload.roomId, payload, assertSession(session)),
      onSuccess: invalidate
    }),
    deleteRoom: useMutation({
      mutationFn: (roomId: number) => schedulerApi.deleteRoom(storeId, roomId, assertSession(session)),
      onSuccess: invalidate
    })
  };
}

export function useSlotMutations(storeId: number) {
  const session = useOptionalSession();
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["slots", storeId] });

  return {
    createSlot: useMutation({
      mutationFn: (payload: { start_at: string }) => schedulerApi.createSlot(storeId, payload, assertSession(session)),
      onSuccess: invalidate
    }),
    updateSlot: useMutation({
      mutationFn: (payload: { slotId: number; start_at: string }) =>
        schedulerApi.updateSlot(storeId, payload.slotId, { start_at: payload.start_at }, assertSession(session)),
      onSuccess: invalidate
    }),
    deleteSlot: useMutation({
      mutationFn: (slotId: number) => schedulerApi.deleteSlot(storeId, slotId, assertSession(session)),
      onSuccess: invalidate
    })
  };
}

export function useBookingMutations(storeId: number, bookingId: number) {
  const session = useOptionalSession();
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["bookings", storeId] });
    await queryClient.invalidateQueries({ queryKey: ["booking", storeId, bookingId] });
  };

  return {
    confirmBooking: useMutation({
      mutationFn: (payload: { start_at: string; preferred_room_id?: number | null }) =>
        schedulerApi.confirmBooking(storeId, bookingId, payload, assertSession(session)),
      onSuccess: invalidate
    }),
    cancelBooking: useMutation({
      mutationFn: () => schedulerApi.cancelBooking(storeId, bookingId, assertSession(session)),
      onSuccess: invalidate
    }),
    completeBooking: useMutation({
      mutationFn: () => schedulerApi.completeBooking(storeId, bookingId, assertSession(session)),
      onSuccess: invalidate
    })
  };
}
