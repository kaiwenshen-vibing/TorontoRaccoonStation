import { SessionProvider, useSession } from "@/providers/SessionProvider";
import { sessionStorage } from "@/lib/storage";
import { render, screen, waitFor } from "@testing-library/react-native";
import { Text } from "react-native";

jest.mock("@/lib/storage", () => ({
  sessionStorage: {
    get: jest.fn(),
    set: jest.fn(),
    clear: jest.fn()
  }
}));

function Probe() {
  const { isReady, session } = useSession();
  return <Text>{isReady ? session?.actorId ?? "empty" : "loading"}</Text>;
}

test("SessionProvider restores persisted session", async () => {
  jest.mocked(sessionStorage.get).mockResolvedValueOnce(
    JSON.stringify({
      actorId: "restored-user",
      allowedStoreIds: [2],
      selectedStoreId: 2
    })
  );

  render(
    <SessionProvider>
      <Probe />
    </SessionProvider>
  );

  await waitFor(() => {
    expect(screen.getByText("restored-user")).toBeTruthy();
  });
});
