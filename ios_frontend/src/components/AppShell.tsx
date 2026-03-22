import { useStoresQuery } from "@/hooks/queries";
import { useSession } from "@/providers/SessionProvider";
import { colors } from "@/theme/tokens";
import { Link, usePathname } from "expo-router";
import { PropsWithChildren, useEffect } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

export function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const { session, setSelectedStoreId, signOut } = useSession();
  const storesQuery = useStoresQuery();

  useEffect(() => {
    if (!session || !storesQuery.data) {
      return;
    }
    const validStoreIds = storesQuery.data.items.map((store) => store.store_id);
    if (!session.selectedStoreId || !validStoreIds.includes(session.selectedStoreId)) {
      void setSelectedStoreId(validStoreIds[0]);
    }
  }, [session, setSelectedStoreId, storesQuery.data]);

  const selectedStoreId = session?.selectedStoreId ?? storesQuery.data?.items[0]?.store_id ?? null;

  return (
    <View style={styles.root}>
      <View style={styles.sidebar}>
        <Text style={styles.brand}>Toronto Raccoon Station</Text>
        <Text style={styles.meta}>Actor: {session?.actorId}</Text>
        <View style={styles.storeList}>
          {storesQuery.data?.items.map((store) => {
            const isSelected = store.store_id === selectedStoreId;
            return (
              <Pressable key={store.store_id} onPress={() => void setSelectedStoreId(store.store_id)} style={[styles.storeChip, isSelected && styles.storeChipSelected]}>
                <Text style={styles.storeChipText}>{store.name}</Text>
              </Pressable>
            );
          })}
        </View>
        {selectedStoreId ? (
          <View style={styles.nav}>
            <NavLink href="/" label="Dashboard" active={pathname === "/"} />
            <NavLink href={`/stores/${selectedStoreId}/bookings`} label="Bookings" active={pathname.includes("/bookings")} />
            <NavLink href={`/stores/${selectedStoreId}/rooms`} label="Rooms" active={pathname.endsWith("/rooms")} />
            <NavLink href={`/stores/${selectedStoreId}/slots`} label="Slots" active={pathname.endsWith("/slots")} />
          </View>
        ) : null}
        <Pressable onPress={() => void signOut()} style={styles.signOut}>
          <Text style={styles.signOutText}>Sign out</Text>
        </Pressable>
      </View>
      <View style={styles.content}>{children}</View>
    </View>
  );
}

function NavLink({ href, label, active }: { href: "/" | `/stores/${number}/bookings` | `/stores/${number}/rooms` | `/stores/${number}/slots`; label: string; active: boolean }) {
  return (
    <Link href={href} asChild style={StyleSheet.flatten([styles.navLink, active && styles.navLinkActive])}>
      <Pressable>
        <Text style={styles.navText}>{label}</Text>
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    flexDirection: "row",
    minHeight: "100%",
    backgroundColor: colors.bg
  },
  sidebar: {
    width: 280,
    backgroundColor: "#171311",
    padding: 20,
    gap: 16
  },
  brand: {
    color: "#fff9f4",
    fontSize: 24,
    fontWeight: "700"
  },
  meta: {
    color: "#c7b8a9"
  },
  storeList: {
    gap: 8
  },
  storeChip: {
    backgroundColor: "#2c2522",
    borderRadius: 12,
    padding: 10
  },
  storeChipSelected: {
    backgroundColor: colors.accent
  },
  storeChipText: {
    color: "#fff9f4",
    fontWeight: "600"
  },
  nav: {
    gap: 8
  },
  navLink: {
    borderRadius: 12,
    padding: 12
  },
  navLinkActive: {
    backgroundColor: "#2c2522"
  },
  navText: {
    color: "#fff9f4",
    fontWeight: "600"
  },
  signOut: {
    marginTop: "auto",
    borderWidth: 1,
    borderColor: "#4a3e38",
    borderRadius: 12,
    padding: 12
  },
  signOutText: {
    color: "#fff9f4"
  },
  content: {
    flex: 1
  }
});
