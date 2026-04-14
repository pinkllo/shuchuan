<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchAuditLogs } from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import AppTimeline from "@/components/AppTimeline.vue";
import type { TimelineItem } from "@/components/AppTimeline.vue";
import { useSessionStore } from "@/stores/session";
import type { AuditLogItem } from "@/types/auth";

const sessionStore = useSessionStore();
const logs = ref<AuditLogItem[]>([]);
const loading = ref(false);

const timelineItems = ref<TimelineItem[]>([]);

function mapLogToTimeline(log: AuditLogItem): TimelineItem {
  return {
    time: log.createdAt,
    content: `[${log.action}] ${log.targetType}${log.targetId ? ` #${log.targetId}` : ''}${log.detail ? ` — ${log.detail}` : ''}`,
    type: log.action.includes('delete') || log.action.includes('disable') ? 'danger'
      : log.action.includes('approve') || log.action.includes('create') ? 'success'
      : 'default'
  };
}

async function loadLogs() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try {
    logs.value = await fetchAuditLogs(token);
    timelineItems.value = logs.value.map(mapLogToTimeline);
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { loading.value = false; }
}

onMounted(loadLogs);
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="page-title">审计日志</h2>
        <p class="page-desc">查看平台关键操作的审计记录。</p>
      </div>
      <el-button plain size="small" @click="loadLogs">刷新</el-button>
    </div>
    <section class="surface-card" v-loading="loading">
      <AppTimeline :items="timelineItems" />
    </section>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--sp-4); }
.page-title { margin: 0 0 var(--sp-1); font-size: var(--text-xl); font-weight: var(--weight-semibold); color: var(--text-primary); }
.page-desc { margin: 0; font-size: var(--text-sm); color: var(--text-secondary); }
</style>
