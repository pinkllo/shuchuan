<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { downloadDelivery, fetchDeliveries } from "@/api/deliveries";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";
import type { DeliveryItem } from "@/types/delivery";

const sessionStore = useSessionStore();
const deliveries = ref<DeliveryItem[]>([]);
const loading = ref(false);
const downloadingId = ref<number | null>(null);

async function loadDeliveries() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  loading.value = true;
  try {
    deliveries.value = await fetchDeliveries(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function handleDownload(item: DeliveryItem) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  downloadingId.value = item.demandId;
  try {
    await downloadDelivery(item.demandId, item.artifactFileName, token);
    ElMessage.success("下载开始");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    downloadingId.value = null;
  }
}

onMounted(loadDeliveries);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>交付下载</h3>
        <p>只有数据使用者可以查看和下载最终交付结果。</p>
      </div>
      <el-button plain @click="loadDeliveries">刷新</el-button>
    </div>

    <el-table :data="deliveries" stripe v-loading="loading">
      <el-table-column prop="demandId" label="需求" width="90" />
      <el-table-column prop="demandTitle" label="需求标题" min-width="220" />
      <el-table-column prop="artifactFileName" label="交付文件" min-width="240" />
      <el-table-column prop="sampleCount" label="样本数" width="110" />
      <el-table-column prop="deliveredAt" label="交付时间" min-width="200" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            link
            :loading="downloadingId === row.demandId"
            @click="handleDownload(row)"
          >
            下载
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
