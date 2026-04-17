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

const roleClasses = computed(() => {
  const map: Record<string, string> = {
    admin: "bg-blue-50 text-blue-600 border border-blue-200",
    provider: "bg-emerald-50 text-emerald-600 border border-emerald-200",
    aggregator: "bg-amber-50 text-amber-600 border border-amber-200",
    consumer: "bg-gray-50 text-gray-500 border border-gray-200"
  };
  return map[sessionStore.role ?? "provider"] ?? "bg-gray-50 text-gray-500 border border-gray-200";
});

async function handleLogout() {
  sessionStore.clearSession();
  ElMessage.success("已退出登录");
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[#fafbfc] font-sans text-gray-900">
    <header class="h-14 w-full bg-white border-b border-gray-200 px-6 flex items-center sticky top-0 z-50">
      <div class="mr-8">
        <span class="text-[15px] font-medium text-gray-900 tracking-wide">数传协同平台</span>
      </div>

      <nav class="flex flex-1 gap-1 h-full items-center">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.name"
          :to="item.path"
          class="h-full flex items-center px-3 text-[13px] font-medium transition-colors duration-150 relative"
          :class="[
            route.name === item.name 
              ? 'text-gray-900 after:absolute after:bottom-0 after:left-3 after:right-3 after:h-0.5 after:bg-gray-900'
              : 'text-gray-500 hover:text-gray-900'
          ]"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <div class="ml-auto flex items-center gap-3">
        <span 
          class="px-2 py-0.5 rounded uppercase text-[11px] font-semibold tracking-wider"
          :class="roleClasses"
        >
          {{ sessionStore.role ? roleLabels[sessionStore.role] : "未登录" }}    
        </span>
        <span class="text-[13px] font-medium text-gray-700 hidden md:inline-block">
          {{ sessionStore.displayName || sessionStore.user?.username }}
        </span>
        <el-button text size="small" @click="handleLogout">退出</el-button>     
      </div>
    </header>

    <main class="flex-1 w-full max-w-[1400px] mx-auto p-6 md:p-8">
      <router-view />
    </main>
  </div>
</template>

