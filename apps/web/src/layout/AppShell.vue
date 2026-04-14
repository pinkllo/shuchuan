<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { filterNavItems } from "@/config/navigation";
import { useSessionStore } from "@/stores/session";
import { roleLabels } from "@/types/auth";

const route = useRoute();
const router = useRouter();
const sessionStore = useSessionStore();

const visibleNavItems = computed(() => filterNavItems(sessionStore.role));

const roleTone = computed(() => {
  const map: Record<string, string> = {
    admin: "info",
    provider: "success",
    aggregator: "warning",
    consumer: "muted"
  };
  return map[sessionStore.role ?? "provider"] ?? "muted";
});

async function handleLogout() {
  sessionStore.clearSession();
  ElMessage.success("已退出登录");
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="shell">
    <header class="shell__nav">
      <div class="shell__brand">
        <span class="shell__logo">数传协同平台</span>
      </div>

      <nav class="shell__tabs">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.name"
          :to="item.path"
          class="shell__tab"
          :class="{ 'shell__tab--active': route.name === item.name }"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <div class="shell__user">
        <span class="shell__role" :class="`shell__role--${roleTone}`">
          {{ sessionStore.role ? roleLabels[sessionStore.role] : "未登录" }}
        </span>
        <span class="shell__username">{{ sessionStore.displayName || sessionStore.user?.username }}</span>
        <el-button text size="small" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <main class="shell__content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Top Nav ── */
.shell__nav {
  display: flex;
  align-items: center;
  height: var(--nav-height);
  padding: 0 var(--sp-6);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.shell__brand {
  margin-right: var(--sp-8);
}

.shell__logo {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

/* ── Nav Tabs ── */
.shell__tabs {
  display: flex;
  gap: var(--sp-1);
  height: 100%;
  align-items: center;
  flex: 1;
}

.shell__tab {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--sp-3);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text-secondary);
  text-decoration: none;
  position: relative;
  transition: color var(--duration-fast) var(--ease-default);
}

.shell__tab:hover {
  color: var(--text-primary);
}

.shell__tab--active {
  color: var(--accent);
}

.shell__tab--active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: var(--sp-3);
  right: var(--sp-3);
  height: 2px;
  background: var(--accent);
  border-radius: 2px 2px 0 0;
}

/* ── User Area ── */
.shell__user {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-left: auto;
}

.shell__role {
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
}

.shell__role--success { background: var(--success-light); color: var(--success); }
.shell__role--warning { background: var(--warning-light); color: var(--warning); }
.shell__role--info { background: var(--info-light); color: var(--info); }
.shell__role--muted { background: var(--bg-hover); color: var(--text-secondary); }

.shell__username {
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text-primary);
}

/* ── Content ── */
.shell__content {
  flex: 1;
  max-width: var(--content-max);
  width: 100%;
  margin: 0 auto;
  padding: var(--sp-6);
  box-sizing: border-box;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .shell__nav {
    padding: 0 var(--sp-3);
    overflow-x: auto;
  }
  .shell__brand {
    margin-right: var(--sp-4);
  }
  .shell__content {
    padding: var(--sp-4);
  }
  .shell__username {
    display: none;
  }
}
</style>
