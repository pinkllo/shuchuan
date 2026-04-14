<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchAuditLogs } from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";
import type { AuditLogItem } from "@/types/auth";

const sessionStore = useSessionStore();
const loading = ref(false);
const logs = ref<AuditLogItem[]>([]);

async function loadLogs() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  loading.value = true;
  try {
    logs.value = await fetchAuditLogs(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

onMounted(loadLogs);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>审计日志</h3>
        <p>记录注册审核、目录发布、需求审批、文件上传、任务推进和交付下载。</p>
      </div>
      <el-button plain @click="loadLogs">刷新</el-button>
    </div>

    <el-table :data="logs" stripe v-loading="loading">
      <el-table-column prop="id" label="日志" width="90" />
      <el-table-column prop="action" label="动作" min-width="180" />
      <el-table-column prop="targetType" label="对象类型" width="140" />
      <el-table-column prop="targetId" label="对象 ID" width="110" />
      <el-table-column prop="actorId" label="操作者" width="110" />
      <el-table-column prop="detail" label="详情" min-width="220" />
      <el-table-column prop="createdAt" label="时间" min-width="200" />
    </el-table>
  </section>
</template>
