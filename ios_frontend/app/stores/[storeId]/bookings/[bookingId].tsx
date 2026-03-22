import { AppShell } from "@/src/components/AppShell";
import { Body, Button, Field, Heading, Panel, Pill, Screen, Subheading } from "@/src/components/ui";
import { useBookingMutations, useBookingQuery } from "@/src/hooks/queries";
import { getBookingStatusLabel } from "@/src/lib/bookingStatus";
import { formatDateTime, isoFromLocalInput } from "@/src/lib/datetime";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Text } from "react-native";

export default function BookingDetailScreen() {
  const params = useLocalSearchParams<{ storeId: string; bookingId: string }>();
  const storeId = Number(params.storeId);
  const bookingId = Number(params.bookingId);
  const bookingQuery = useBookingQuery(storeId, bookingId);
  const mutations = useBookingMutations(storeId, bookingId);
  const [startAt, setStartAt] = useState("");
  const [preferredRoomId, setPreferredRoomId] = useState("");

  const onConfirm = async () => {
    const isoValue = isoFromLocalInput(startAt);
    if (!isoValue) {
      return;
    }
    await mutations.confirmBooking.mutateAsync({
      start_at: isoValue,
      preferred_room_id: preferredRoomId ? Number(preferredRoomId) : null
    });
  };

  const booking = bookingQuery.data;

  return (
    <AppShell>
      <Screen>
        <Panel>
          <Heading>Booking #{bookingId}</Heading>
          {booking ? <Pill label={getBookingStatusLabel(booking.booking_status_id)} tone={booking.has_conflict ? "danger" : "default"} /> : null}
          {bookingQuery.isLoading ? <Text>Loading booking...</Text> : null}
          {bookingQuery.error ? <Text>{bookingQuery.error.message}</Text> : null}
          {booking ? (
            <>
              <Body>Start: {formatDateTime(booking.start_at)}</Body>
              <Body>End: {formatDateTime(booking.end_at)}</Body>
              <Body>Target month: {booking.target_month ?? "Unset"}</Body>
              <Body>Clients: {booking.client_ids.join(", ") || "None"}</Body>
              <Body>Script: {booking.script_id ?? "Unset"}</Body>
              <Body>Conflict count: {booking.conflict_count}</Body>
            </>
          ) : null}
        </Panel>
        <Panel>
          <Subheading>Confirm booking</Subheading>
          <Field
            label="Start time"
            value={startAt}
            onChangeText={setStartAt}
            placeholder="2026-03-22T18:30:00-04:00"
          />
          <Field
            label="Preferred room ID"
            value={preferredRoomId}
            onChangeText={setPreferredRoomId}
            placeholder="12"
          />
          <Button label="Confirm" onPress={onConfirm} disabled={mutations.confirmBooking.isPending} />
        </Panel>
        <Panel>
          <Subheading>Lifecycle</Subheading>
          <Button
            label="Cancel booking"
            onPress={() => mutations.cancelBooking.mutate()}
            variant="secondary"
            disabled={mutations.cancelBooking.isPending}
          />
          <Button
            label="Mark complete"
            onPress={() => mutations.completeBooking.mutate()}
            variant="secondary"
            disabled={mutations.completeBooking.isPending}
          />
          {mutations.confirmBooking.error ? <Text>{mutations.confirmBooking.error.message}</Text> : null}
          {mutations.cancelBooking.error ? <Text>{mutations.cancelBooking.error.message}</Text> : null}
          {mutations.completeBooking.error ? <Text>{mutations.completeBooking.error.message}</Text> : null}
        </Panel>
      </Screen>
    </AppShell>
  );
}
