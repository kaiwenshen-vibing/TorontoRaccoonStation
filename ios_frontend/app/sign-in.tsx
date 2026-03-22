import { Button, Field, Heading, Panel, Screen } from "@/src/components/ui";
import { useSession } from "@/src/providers/SessionProvider";
import { useRouter } from "expo-router";
import { useState } from "react";
import { Text } from "react-native";

export default function SignInScreen() {
  const { signIn } = useSession();
  const router = useRouter();
  const [actorId, setActorId] = useState("");
  const [allowedStoreIds, setAllowedStoreIds] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onSubmit = async () => {
    setError("");
    const storeIds = allowedStoreIds
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isInteger(item) && item > 0);

    if (!actorId.trim() || storeIds.length === 0) {
      setError("Enter an actor ID and at least one numeric store ID.");
      return;
    }

    setIsSubmitting(true);
    try {
      await signIn({
        actorId: actorId.trim(),
        allowedStoreIds: storeIds,
        selectedStoreId: storeIds[0]
      });
      router.replace("/");
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Unable to start session.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Screen>
      <Panel>
        <Heading>Staff Sign-In</Heading>
        <Text>
          Use the backend header model directly. This temporary session shim keeps the web build moving
          without adding auth endpoints first.
        </Text>
      </Panel>
      <Panel>
        <Field label="Actor ID" value={actorId} onChangeText={setActorId} placeholder="kevin-admin" />
        <Field
          label="Allowed store IDs"
          value={allowedStoreIds}
          onChangeText={setAllowedStoreIds}
          placeholder="1,2"
        />
        {error ? <Text style={{ color: "#9d2f12", fontWeight: "600" }}>{error}</Text> : null}
        <Button label={isSubmitting ? "Starting session..." : "Start session"} onPress={onSubmit} disabled={isSubmitting} />
      </Panel>
    </Screen>
  );
}
