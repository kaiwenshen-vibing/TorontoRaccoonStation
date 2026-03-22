import { AppShell } from "@/src/components/AppShell";
import { Body, Button, Field, Heading, Panel, Pill, Screen } from "@/src/components/ui";
import { useBookingsQuery } from "@/src/hooks/queries";
import { getBookingStatusLabel } from "@/src/lib/bookingStatus";
import { formatDateTime } from "@/src/lib/datetime";
import { Link, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

export default function BookingsScreen() {
  const params = useLocalSearchParams<{ storeId: string }>();
  const storeId = Number(params.storeId);
  const [statusFilter, setStatusFilter] = useState("");
  const [monthFilter, setMonthFilter] = useState("");
  const [conflictOnly, setConflictOnly] = useState(false);
  const query = useBookingsQuery(storeId, {
    bookingStatusId: statusFilter ? Number(statusFilter) : undefined,
    targetMonth: monthFilter || undefined,
    hasConflict: conflictOnly ? true : undefined
  });

  return (
    <AppShell>
      <Screen>
        <Panel>
          <Heading>Bookings</Heading>
          <Body>Filter by seeded booking status IDs: 1 incomplete, 2 scheduled, 3 cancelled, 4 completed.</Body>
        </Panel>
        <Panel>
          <Field label="Status ID" value={statusFilter} onChangeText={setStatusFilter} placeholder="2" />
          <Field label="Target month" value={monthFilter} onChangeText={setMonthFilter} placeholder="2026-03-01" />
          <Button
            label={conflictOnly ? "Showing conflicts only" : "Show conflicts only"}
            onPress={() => setConflictOnly((value) => !value)}
            variant="secondary"
          />
        </Panel>
        <Panel>
          {query.isLoading ? <Text>Loading bookings...</Text> : null}
          {query.error ? <Text>{query.error.message}</Text> : null}
          {query.data?.items.map((booking) => (
            <Link key={booking.booking_id} href={`/stores/${storeId}/bookings/${booking.booking_id}`} asChild>
              <Pressable style={{ gap: 8, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: "#d8cfc0" }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <Text style={{ fontWeight: "700" }}>Booking #{booking.booking_id}</Text>
                  <Pill label={getBookingStatusLabel(booking.booking_status_id)} tone={booking.has_conflict ? "danger" : "default"} />
                </View>
                <Text>{formatDateTime(booking.start_at)}</Text>
                <Text>Clients: {booking.client_ids.join(", ") || "None"}</Text>
                <Text>Script: {booking.script_id ?? "Unset"}</Text>
                {booking.has_conflict ? <Text>Conflicts: {booking.conflict_booking_ids.join(", ")}</Text> : null}
              </Pressable>
            </Link>
          ))}
          {query.data && query.data.items.length === 0 ? <Text>No bookings match the current filters.</Text> : null}
        </Panel>
      </Screen>
    </AppShell>
  );
}
