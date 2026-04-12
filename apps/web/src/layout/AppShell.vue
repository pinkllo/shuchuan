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

const currentNav = computed(() => {
  const routeName = typeof route.name === "string" ? route.name : "";
  return visibleNavItems.value.find((item) => item.name === routeName) ?? visibleNavItems.value[0] ?? null;
});

const roleColor = computed(() => {
  const map: Record<string, string> = {
    admin: "#5d2e8c",
    provider: "#0f5860",
    aggregator: "#8f4c16",
    consumer: "#1b4d8f"
  };
  return map[sessionStore.role ?? "provider"] ?? "#0f5860";
});

const roleBg = computed(() => {
  const map: Record<string, string> = {
    admin: "rgba(93, 46, 140, 0.14)",
    provider: "rgba(24, 119, 123, 0.12)",
    aggregator: "rgba(200, 140, 60, 0.14)",
    consumer: "rgba(50, 100, 180, 0.12)"
  };
  return map[sessionStore.role ?? "provider"] ?? "rgba(24, 119, 123, 0.12)";
});

async function handleLogout() {
  sessionStore.clearSession();
  ElMessage.success("已退出登录");
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="shell">
    <header class="shell__top-nav">
      <div class="shell__brand">
        <h1>数传协同平台</h1>
        <p>真实鉴权、真实链路、显式失败</p>
      </div>

      <nav class="shell__nav">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.name"
          :to="item.path"
          class="shell__nav-item"
          :class="{ 'is-active': route.name === item.name }"
        >
          <component :is="item.icon" class="shell__nav-icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="shell__user-actions">
        <span
          class="shell__badge"
          :style="{ background: roleBg, color: roleColor }"
        >
          {{ sessionStore.role ? roleLabels[sessionStore.role] : "未登录" }}
        </span>
        <div class="shell__user-meta">
          <strong>{{ sessionStore.displayName || sessionStore.user?.username }}</strong>
          <small>{{ sessionStore.user?.email ?? sessionStore.user?.username }}</small>
        </div>
        <el-button link type="primary" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <div class="shell__main">
      <header class="shell__page-header">
        <h2>{{ String(route.meta.title ?? currentNav?.label ?? "平台页面") }}</h2>
        <p class="shell__summary">
          {{ String(route.meta.summary ?? currentNav?.hint ?? "基于角色权限访问当前页面。") }}
        </p>
      </header>

      <main class="shell__content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f7f9fa;
}

.shell__top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #ebedf0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.shell__brand h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: 0.5px;
}

.shell__brand p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.shell__nav {
  display: flex;
  gap: 32px;
  align-items: center;
  height: 100%;
}

.shell__nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
  color: #5c6b77;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  position: relative;
  transition: color 0.2s;
}

.shell__nav-item:hover {
  color: var(--accent-strong, #0f5860);
}

.shell__nav-item.is-active {
  color: var(--accent-strong, #0f5860);
}

.shell__nav-item.is-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: var(--accent-strong, #0f5860);
  border-radius: 3px 3px 0 0;
}

.shell__nav-icon {
  width: 18px;
  height: 18px;
}

.shell__user-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.shell__user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.shell__user-meta strong {
  font-size: 14px;
  color: #111827;
}

.shell__user-meta small {
  font-size: 12px;
  color: #6b7280;
}

.shell__badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.shell__main {
  flex: 1;
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.shell__page-header {
  margin-bottom: 24px;
}

.shell__page-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #1a202c;
  font-weight: 600;
}

.shell__summary {
  margin: 0;
  font-size: 14px;
  color: #718096;
}

.shell__content {
  min-width: 0;
}

@media (max-width: 768px) {
  .shell__top-nav {
    padding: 0 16px;
    overflow-x: auto;
  }
  .shell__main {
    padding: 16px;
  }
}
</style>
