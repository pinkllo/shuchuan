<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import { fetchProcessors } from "@/api/processors";
import StatusPill from "@/components/StatusPill.vue";
import { useSessionStore } from "@/stores/session";
import type { Processor } from "@/types/processor";

const sessionStore = useSessionStore();

const processors = ref<Processor[]>([]);
const loading = ref(false);

async function loadProcessors() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try {
    processors.value = await fetchProcessors(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

onMounted(loadProcessors);
</script>

<template>
  <div class="page-grid">
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>处理器管理</h3>
          <p>查看所有已注册外部处理服务的任务类型、端点和在线状态。</p>
        </div>
        <div>
          <el-button plain @click="loadProcessors">刷新</el-button>
        </div>
      </div>
      <el-table :data="processors" stripe v-loading="loading">
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="taskType" label="任务类型" width="140" />
        <el-table-column prop="description" label="描述" min-width="180" />
        <el-table-column prop="endpointUrl" label="端点地址" min-width="220" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusPill
              :label="row.status === 'online' ? '在线' : '离线'"
              :tone="row.status === 'online' ? 'good' : 'warn'"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastHeartbeatAt" label="最后心跳" width="180" />
        <el-table-column prop="registeredAt" label="注册时间" width="180" />
      </el-table>
    </section>
  </div>
</template>
