import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useSessionStore } from "@/stores/session";

describe("session store", () => {
  beforeEach(() => {
    sessionStorage.clear();
    setActivePinia(createPinia());
  });

  it("persists the authenticated user and admin role", () => {
    const store = useSessionStore();

    store.setSession({
      accessToken: "token-123",
      user: {
        id: 1,
        username: "admin",
        displayName: "管理员",
        role: "admin"
      }
    });

    expect(store.isAuthenticated).toBe(true);
    expect(store.role).toBe("admin");
    expect(JSON.parse(sessionStorage.getItem("dt-platform-session") ?? "{}").accessToken).toBe("token-123");
  });

  it("clears the stored token and user", () => {
    const store = useSessionStore();

    store.setSession({
      accessToken: "token-123",
      user: {
        id: 2,
        username: "provider_a",
        displayName: "提供者 A",
        role: "provider"
      }
    });
    store.clearSession();

    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(sessionStorage.getItem("dt-platform-session")).toBeNull();
  });
});
