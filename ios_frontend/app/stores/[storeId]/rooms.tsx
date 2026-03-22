import { AppShell } from "@/src/components/AppShell";
import { Body, Button, Field, Heading, Panel, Screen, Subheading } from "@/src/components/ui";
import { useRoomMutations, useRoomsQuery } from "@/src/hooks/queries";
import { useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { Text, View } from "react-native";

export default function RoomsScreen() {
  const params = useLocalSearchParams<{ storeId: string }>();
  const storeId = Number(params.storeId);
  const roomsQuery = useRoomsQuery(storeId);
  const { createRoom, updateRoom, deleteRoom } = useRoomMutations(storeId);
  const [newName, setNewName] = useState("");

  const create = async () => {
    if (!newName.trim()) {
      return;
    }
    await createRoom.mutateAsync({ name: newName.trim() });
    setNewName("");
  };

  return (
    <AppShell>
      <Screen>
        <Panel>
          <Heading>Rooms</Heading>
          <Body>Create, rename, deactivate, and remove store rooms.</Body>
        </Panel>
        <Panel>
          <Subheading>Create room</Subheading>
          <Field label="Room name" value={newName} onChangeText={setNewName} placeholder="Blue Lounge" />
          <Button label="Create room" onPress={create} disabled={createRoom.isPending} />
          {createRoom.error ? <Text>{createRoom.error.message}</Text> : null}
        </Panel>
        <Panel>
          {roomsQuery.isLoading ? <Text>Loading rooms...</Text> : null}
          {roomsQuery.error ? <Text>{roomsQuery.error.message}</Text> : null}
          {roomsQuery.data?.items.map((room) => (
            <View key={room.store_room_id} style={{ gap: 8, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: "#d8cfc0" }}>
              <Text style={{ fontWeight: "700" }}>
                #{room.store_room_id} {room.name}
              </Text>
              <Text>{room.is_active ? "Active" : "Inactive"}</Text>
              <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                <Button
                  label="Toggle active"
                  onPress={() => updateRoom.mutate({ roomId: room.store_room_id, is_active: !room.is_active })}
                  variant="secondary"
                />
                <Button
                  label="Rename to 'Ready Room'"
                  onPress={() => updateRoom.mutate({ roomId: room.store_room_id, name: "Ready Room" })}
                  variant="secondary"
                />
                <Button label="Delete" onPress={() => deleteRoom.mutate(room.store_room_id)} variant="danger" />
              </View>
            </View>
          ))}
          {roomsQuery.data && roomsQuery.data.items.length === 0 ? <Text>No rooms configured yet.</Text> : null}
        </Panel>
      </Screen>
    </AppShell>
  );
}
