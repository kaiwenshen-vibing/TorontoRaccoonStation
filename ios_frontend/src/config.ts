const fallbackApiBaseUrl = "http://localhost:8080/api/v1";

export const appConfig = {
  apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? fallbackApiBaseUrl,
  defaultActorId: process.env.EXPO_PUBLIC_DEFAULT_ACTOR_ID ?? "",
  defaultStoreIds: process.env.EXPO_PUBLIC_DEFAULT_STORE_IDS ?? ""
};
