import { colors } from "@/theme/tokens";
import { PropsWithChildren } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

export function Screen({ children }: PropsWithChildren) {
  return <ScrollView contentContainerStyle={styles.screen}>{children}</ScrollView>;
}

export function Panel({ children }: PropsWithChildren) {
  return <View style={styles.panel}>{children}</View>;
}

export function Heading({ children }: PropsWithChildren) {
  return <Text style={styles.heading}>{children}</Text>;
}

export function Subheading({ children }: PropsWithChildren) {
  return <Text style={styles.subheading}>{children}</Text>;
}

export function Body({ children }: PropsWithChildren) {
  return <Text style={styles.body}>{children}</Text>;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  disabled = false
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}) {
  const style = [styles.button, buttonVariants[variant], disabled && styles.buttonDisabled];
  const textStyle = [styles.buttonText, variant === "secondary" && styles.buttonTextSecondary];
  return (
    <Pressable accessibilityRole="button" onPress={onPress} disabled={disabled} style={style}>
      <Text style={textStyle}>{label}</Text>
    </Pressable>
  );
}

export function Field({
  label,
  value,
  onChangeText,
  placeholder
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput value={value} onChangeText={onChangeText} placeholder={placeholder} style={styles.input} />
    </View>
  );
}

export function Pill({ label, tone = "default" }: { label: string; tone?: "default" | "success" | "danger" | "warning" }) {
  return (
    <View style={[styles.pill, pillVariants[tone]]}>
      <Text style={styles.pillText}>{label}</Text>
    </View>
  );
}

const buttonVariants = StyleSheet.create({
  primary: { backgroundColor: colors.accent },
  secondary: { backgroundColor: colors.surfaceMuted },
  danger: { backgroundColor: colors.danger }
});

const pillVariants = StyleSheet.create({
  default: { backgroundColor: colors.surfaceMuted },
  success: { backgroundColor: "#d9eadf" },
  danger: { backgroundColor: "#f2d2ce" },
  warning: { backgroundColor: "#f4e6bb" }
});

const styles = StyleSheet.create({
  screen: {
    flexGrow: 1,
    padding: 20,
    gap: 16,
    backgroundColor: colors.bg
  },
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
    gap: 12
  },
  heading: {
    fontSize: 28,
    fontWeight: "700",
    color: colors.text
  },
  subheading: {
    fontSize: 18,
    fontWeight: "600",
    color: colors.text
  },
  body: {
    fontSize: 15,
    color: colors.textMuted
  },
  field: {
    gap: 6
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.text
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: colors.text
  },
  button: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 11
  },
  buttonDisabled: {
    opacity: 0.6
  },
  buttonText: {
    color: "#fff9f4",
    fontWeight: "700"
  },
  buttonTextSecondary: {
    color: colors.text
  },
  pill: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: "flex-start"
  },
  pillText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700"
  }
});
