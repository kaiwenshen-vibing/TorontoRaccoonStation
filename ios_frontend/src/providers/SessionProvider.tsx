import { appConfig } from "@/config";
import { sessionStorage } from "@/lib/storage";
import type { SessionState } from "@/types/api";
import { PropsWithChildren, createContext, useContext, useEffect, useState } from "react";

type SessionContextValue = {
  isReady: boolean;
  session: SessionState | null;
  signIn: (nextSession: SessionState) => Promise<void>;
  signOut: () => Promise<void>;
  setSelectedStoreId: (storeId: number) => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

function getDefaultSession(): SessionState | null {
  if (!appConfig.defaultActorId || !appConfig.defaultStoreIds) {
    return null;
  }
  const allowedStoreIds = appConfig.defaultStoreIds
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0);
  if (allowedStoreIds.length === 0) {
    return null;
  }
  return {
    actorId: appConfig.defaultActorId,
    allowedStoreIds,
    selectedStoreId: allowedStoreIds[0]
  };
}

export function SessionProvider({ children }: PropsWithChildren) {
  const [isReady, setIsReady] = useState(false);
  const [session, setSession] = useState<SessionState | null>(null);

  useEffect(() => {
    async function loadSession() {
      const stored = await sessionStorage.get();
      if (stored) {
        setSession(JSON.parse(stored) as SessionState);
        setIsReady(true);
        return;
      }

      const fallback = getDefaultSession();
      if (fallback) {
        setSession(fallback);
        await sessionStorage.set(JSON.stringify(fallback));
      }
      setIsReady(true);
    }

    void loadSession();
  }, []);

  async function persist(nextSession: SessionState | null) {
    setSession(nextSession);
    if (nextSession) {
      await sessionStorage.set(JSON.stringify(nextSession));
    } else {
      await sessionStorage.clear();
    }
  }

  const value: SessionContextValue = {
    isReady,
    session,
    async signIn(nextSession) {
      await persist(nextSession);
    },
    async signOut() {
      await persist(null);
    },
    async setSelectedStoreId(storeId) {
      if (!session) {
        return;
      }
      await persist({ ...session, selectedStoreId: storeId });
    }
  };

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
