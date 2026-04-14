<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchDeliveries, downloadDelivery } from "@/api/deliveries";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";
import type { DeliveryItem } from "@/types/delivery";

const sessionStore = useSessionStore();
const deliveries = ref<DeliveryItem[]>([]);
const loading = ref(false);

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try { deliveries.value = await fetchDeliveries(token); }
  catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { loading.value = false; }
}

async function handleDownload(item: DeliveryItem) {
  const token = sessionStore.accessToken;
  if (!token) return;
  try { await downloadDelivery(item.demandId, token); }
  catch (error) { ElMessage.error(getErrorMessage(error)); }
}

onMounted(loadPage);
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2 class="page-title">交付下载</h2>
        <p class="page-desc">查看并下载已完成的交付文件。</p>
      </div>
      <el-button plain size="small" @click="loadPage">刷新</el-button>
    </div>
    <section class="surface-card">
      <el-table :data="deliveries" stripe v-loading="loading">
        <el-table-column prop="demandTitle" label="需求标题" min-width="220" />
        <el-table-column prop="artifactFileName" label="文件名" min-width="200" />
        <el-table-column prop="sampleCount" label="样本数" width="110" />
        <el-table-column prop="deliveredAt" label="交付时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleDownload(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--sp-4); }
.page-title { margin: 0 0 var(--sp-1); font-size: var(--text-xl); font-weight: var(--weight-semibold); color: var(--text-primary); }
.page-desc { margin: 0; font-size: var(--text-sm); color: var(--text-secondary); }
</style>
