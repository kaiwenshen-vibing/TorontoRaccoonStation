import { AppShell } from "@/src/components/AppShell";
import { Body, Button, Field, Heading, Panel, Screen, Subheading } from "@/src/components/ui";
import { useSlotMutations, useSlotsQuery } from "@/src/hooks/queries";
import { formatDateTime, isoFromLocalInput } from "@/src/lib/datetime";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

export default function SlotsScreen() {
  const params = useLocalSearchParams<{ storeId: string }>();
  const storeId = Number(params.storeId);
  const slotsQuery = useSlotsQuery(storeId);
  const { createSlot, updateSlot, deleteSlot } = useSlotMutations(storeId);
  const [startAt, setStartAt] = useState("");

  const create = async () => {
    const isoValue = isoFromLocalInput(startAt);
    if (!isoValue) {
      return;
    }
    await createSlot.mutateAsync({ start_at: isoValue });
    setStartAt("");
  };

  return (
    <AppShell>
      <Screen>
        <Panel>
          <Heading>Slots</Heading>
          <Body>Slots are the schedulable time anchors used when bookings are confirmed.</Body>
        </Panel>
        <Panel>
          <Subheading>Create slot</Subheading>
          <Field
            label="Start time"
            value={startAt}
            onChangeText={setStartAt}
            placeholder="2026-03-22T18:30:00-04:00"
          />
          <Button label="Create slot" onPress={create} disabled={createSlot.isPending} />
          {createSlot.error ? <Text>{createSlot.error.message}</Text> : null}
        </Panel>
        <Panel>
          {slotsQuery.isLoading ? <Text>Loading slots...</Text> : null}
          {slotsQuery.error ? <Text>{slotsQuery.error.message}</Text> : null}
          {slotsQuery.data?.items.map((slot) => (
            <View key={slot.slot_id} style={{ gap: 8, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#d8cfc0" }}>
              <Text style={{ fontWeight: "700" }}>Slot #{slot.slot_id}</Text>
              <Text>{formatDateTime(slot.start_at)}</Text>
              <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                <Button
                  label="Shift +1 hour"
                  onPress={() => {
                    const shifted = new Date(slot.start_at);
                    shifted.setHours(shifted.getHours() + 1);
                    updateSlot.mutate({ slotId: slot.slot_id, start_at: shifted.toISOString() });
                  }}
                  variant="secondary"
                />
                <Button label="Delete" onPress={() => deleteSlot.mutate(slot.slot_id)} variant="danger" />
              </View>
            </View>
          ))}
          {slotsQuery.data && slotsQuery.data.items.length === 0 ? <Text>No slots configured yet.</Text> : null}
        </Panel>
      </Screen>
    </AppShell>
  );
}
