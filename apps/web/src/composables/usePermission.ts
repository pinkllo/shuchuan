import { computed } from "vue";

import { useSessionStore } from "@/stores/session";
import type { UserRole } from "@/types/auth";

export type Action =
  | "catalog.create"
  | "catalog.publish"
  | "catalog.archive"
  | "demand.create"
  | "demand.approve"
  | "demand.upload"
  | "task.create"
  | "task.manage"
  | "delivery.download"
  | "admin.registration.review"
  | "admin.user.manage"
  | "admin.audit.read"
  | "integration.configure";

const actionRoles: Record<Action, readonly UserRole[]> = {
  "catalog.create": ["provider"],
  "catalog.publish": ["provider"],
  "catalog.archive": ["provider"],
  "demand.create": ["aggregator"],
  "demand.approve": ["provider"],
  "demand.upload": ["provider"],
  "task.create": ["aggregator"],
  "task.manage": ["aggregator"],
  "delivery.download": ["consumer"],
  "admin.registration.review": ["admin"],
  "admin.user.manage": ["admin"],
  "admin.audit.read": ["admin"],
  "integration.configure": ["aggregator"]
};

export function usePermission() {
  const session = useSessionStore();

  const isAuthenticated = computed(() => session.isAuthenticated);
  const isAdmin = computed(() => session.role === "admin");
  const isProvider = computed(() => session.role === "provider");
  const isAggregator = computed(() => session.role === "aggregator");
  const isConsumer = computed(() => session.role === "consumer");
  const role = computed(() => session.role);

  function can(action: Action): boolean {
    const currentRole = session.role;
    if (!currentRole) {
      return false;
    }

    return actionRoles[action].includes(currentRole);
  }

  return {
    can,
    isAdmin,
    isAuthenticated,
    isProvider,
    isAggregator,
    isConsumer,
    role
  };
}
