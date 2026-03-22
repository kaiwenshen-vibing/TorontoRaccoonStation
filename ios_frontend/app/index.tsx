import { AppShell } from "@/src/components/AppShell";
import { Body, Button, Heading, Panel, Screen, Subheading } from "@/src/components/ui";
import { useBookingsQuery, useRoomsQuery, useSlotsQuery, useStoresQuery } from "@/src/hooks/queries";
import { useSession } from "@/src/providers/SessionProvider";
import { useRouter } from "expo-router";
import { View } from "react-native";

export default function DashboardScreen() {
  const { session } = useSession();
  const router = useRouter();
  const storesQuery = useStoresQuery();
  const storeId = session?.selectedStoreId ?? storesQuery.data?.items[0]?.store_id ?? 0;
  const bookingsQuery = useBookingsQuery(storeId, {});
  const roomsQuery = useRoomsQuery(storeId);
  const slotsQuery = useSlotsQuery(storeId);

  return (
    <AppShell>
      <Screen>
        <Panel>
          <Heading>Scheduler Dashboard</Heading>
          <Body>
            Web-first Expo shell over the current FastAPI API. Pick a store from the left rail and move
            between bookings, rooms, and slots without changing app foundations later.
          </Body>
        </Panel>
        <View style={{ flexDirection: "row", gap: 16, flexWrap: "wrap" }}>
          <Panel>
            <Subheading>Bookings</Subheading>
            <Body>{bookingsQuery.data?.total ?? 0} visible records</Body>
          </Panel>
          <Panel>
            <Subheading>Rooms</Subheading>
            <Body>{roomsQuery.data?.total ?? 0} configured rooms</Body>
          </Panel>
          <Panel>
            <Subheading>Slots</Subheading>
            <Body>{slotsQuery.data?.total ?? 0} published slots</Body>
          </Panel>
        </View>
        {storeId ? (
          <Panel>
            <Subheading>Jump to work</Subheading>
            <Button label="Open bookings" onPress={() => void router.push(`/stores/${storeId}/bookings`)} />
          </Panel>
        ) : null}
      </Screen>
    </AppShell>
  );
}
