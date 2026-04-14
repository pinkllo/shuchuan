import { defineStore } from "pinia";

import { fetchCurrentUser } from "@/api/auth";
import { roleLabels, type SessionPayload, type SessionSnapshot, type SessionUser, type UserRole } from "@/types/auth";

interface SessionState extends SessionSnapshot {
  restoring: boolean;
  restored: boolean;
}

const SESSION_KEY = "dt-platform-session";

const EMPTY_SNAPSHOT: SessionSnapshot = {
  accessToken: null,
  user: null
};

export const useSessionStore = defineStore("session", {
  state: (): SessionState => ({
    ...readPersistedSnapshot(),
    restoring: false,
    restored: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
    role: (state): UserRole | null => state.user?.role ?? null,
    roleLabel: (state) => (state.user ? roleLabels[state.user.role] : "未登录"),
    displayName: (state) => state.user?.displayName ?? ""
  },
  actions: {
    setSession(payload: SessionPayload | SessionSnapshot) {
      const snapshot = normalizeSnapshot(payload);
      this.accessToken = snapshot.accessToken;
      this.user = snapshot.user;
      this.restored = true;
      persistSnapshot(snapshot);
    },
    clearSession() {
      this.accessToken = null;
      this.user = null;
      this.restoring = false;
      this.restored = true;
      clearPersistedSnapshot();
    },
    async restoreSession() {
      if (this.restoring || this.restored) {
        return;
      }
      if (!this.accessToken) {
        this.restored = true;
        return;
      }

      this.restoring = true;
      try {
        this.user = await fetchCurrentUser(this.accessToken);
        this.restored = true;
        persistSnapshot({
          accessToken: this.accessToken,
          user: this.user
        });
      } catch (error) {
        this.clearSession();
        throw error;
      } finally {
        this.restoring = false;
      }
    }
  }
});

function readPersistedSnapshot(): SessionSnapshot {
  if (typeof window === "undefined") {
    return { ...EMPTY_SNAPSHOT };
  }

  const raw = window.sessionStorage.getItem(SESSION_KEY);
  if (raw === null) {
    return { ...EMPTY_SNAPSHOT };
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error("会话缓存已损坏，无法解析", { cause: error });
  }

  return normalizeSnapshot(parsed);
}

function persistSnapshot(snapshot: SessionSnapshot) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(SESSION_KEY, JSON.stringify(snapshot));
}

function clearPersistedSnapshot() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(SESSION_KEY);
}

function normalizeSnapshot(value: unknown): SessionSnapshot {
  if (!isRecord(value)) {
    throw new Error("会话缓存格式无效");
  }

  const accessToken = value.accessToken;
  const user = value.user;

  if (accessToken !== null && accessToken !== undefined && typeof accessToken !== "string") {
    throw new Error("会话 accessToken 格式无效");
  }

  return {
    accessToken: accessToken ?? null,
    user: user === null || user === undefined ? null : normalizeUser(user)
  };
}

function normalizeUser(value: unknown): SessionUser {
  if (!isRecord(value)) {
    throw new Error("会话 user 格式无效");
  }

  if (typeof value.id !== "number") {
    throw new Error("会话 user.id 格式无效");
  }
  if (typeof value.username !== "string") {
    throw new Error("会话 user.username 格式无效");
  }
  if (typeof value.displayName !== "string") {
    throw new Error("会话 user.displayName 格式无效");
  }
  if (!isUserRole(value.role)) {
    throw new Error("会话 user.role 格式无效");
  }
  if (value.email !== undefined && value.email !== null && typeof value.email !== "string") {
    throw new Error("会话 user.email 格式无效");
  }
  if (value.status !== undefined && value.status !== null && value.status !== "active" && value.status !== "disabled") {
    throw new Error("会话 user.status 格式无效");
  }

  return {
    id: value.id,
    username: value.username,
    displayName: value.displayName,
    role: value.role,
    email: typeof value.email === "string" ? value.email : undefined,
    status: value.status === "active" || value.status === "disabled" ? value.status : undefined
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === "[object Object]";
}

function isUserRole(value: unknown): value is UserRole {
  return value === "admin" || value === "provider" || value === "aggregator" || value === "consumer";
}
