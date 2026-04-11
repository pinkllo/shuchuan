<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { navItems } from '@/config/navigation'
import { useSessionStore, roleLabels } from '@/stores/session'
import { usePermission } from '@/composables/usePermission'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const { role } = usePermission()

const currentNav = computed(() =>
  navItems.find((item) => item.name === route.name) ?? navItems[0]
)

const roleColor = computed(() => {
  const map: Record<string, string> = {
    provider: '#0f5860',
    aggregator: '#5a3e1b',
    consumer: '#1b4d8f'
  }
  return map[sessionStore.role] ?? '#0f5860'
})

const roleBg = computed(() => {
  const map: Record<string, string> = {
    provider: 'rgba(24, 119, 123, 0.12)',
    aggregator: 'rgba(200, 140, 60, 0.14)',
    consumer: 'rgba(50, 100, 180, 0.12)'
  }
  return map[sessionStore.role] ?? 'rgba(24, 119, 123, 0.12)'
})

function handleLogout() {
  sessionStore.logout()
  ElMessage.success('已退出')
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <header class="shell__top-nav">
      <div class="shell__brand">
        <h1>数传协同平台</h1>
      </div>

      <nav class="shell__nav">
        <router-link
          v-for="item in navItems"
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
          {{ roleLabels[sessionStore.role] }}
        </span>
        <el-button link type="primary" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <div class="shell__main">
      <header class="shell__page-header">
        <h2>{{ String(route.meta.title ?? currentNav.label) }}</h2>
        <p class="shell__summary">
          {{ String(route.meta.summary ?? currentNav.hint) }}
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
