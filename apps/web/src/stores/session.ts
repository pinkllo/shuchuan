import { defineStore } from "pinia";

export type UserRole = "provider" | "aggregator" | "consumer";

export interface SessionState {
  loggedIn: boolean;
  name: string;
  role: UserRole;
}

const SESSION_KEY = "dt-platform-session";

export const roleLabels: Record<UserRole, string> = {
  provider: "数据提供者",
  aggregator: "数据汇聚者",
  consumer: "数据使用者"
};

function defaultSession(): SessionState {
  return { loggedIn: false, name: "", role: "aggregator" };
}

export function readSession(): SessionState {
  if (typeof window === "undefined") {
    return defaultSession();
  }

  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (!raw) {
    return defaultSession();
  }

  try {
    return JSON.parse(raw) as SessionState;
  } catch {
    return defaultSession();
  }
}

function persistSession(session: SessionState) {
  if (typeof window !== "undefined") {
    window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }
}

export const useSessionStore = defineStore("session", {
  state: (): SessionState => readSession(),
  getters: {
    roleLabel: (state) => roleLabels[state.role]
  },
  actions: {
    login(role: UserRole) {
      this.$state = {
        loggedIn: true,
        name: roleLabels[role],
        role
      };
      persistSession(this.$state);
    },
    logout() {
      this.$state = defaultSession();
      persistSession(this.$state);
    }
  }
});
