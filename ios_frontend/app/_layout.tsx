import { QueryProvider } from "@/src/providers/QueryProvider";
import { SessionProvider, useSession } from "@/src/providers/SessionProvider";
import { Redirect, Stack, usePathname } from "expo-router";
import { ActivityIndicator, View } from "react-native";

function GuardedStack() {
  const { isReady, session } = useSession();
  const pathname = usePathname();

  if (!isReady) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator />
      </View>
    );
  }

  if (!session && pathname !== "/sign-in") {
    return <Redirect href="/sign-in" />;
  }

  if (session && pathname === "/sign-in") {
    return <Redirect href="/" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}

export default function RootLayout() {
  return (
    <SessionProvider>
      <QueryProvider>
        <GuardedStack />
      </QueryProvider>
    </SessionProvider>
  );
}
