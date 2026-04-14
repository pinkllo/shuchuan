<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchProcessors } from "@/api/processors";
import { getErrorMessage } from "@/api/http";
import MasterDetail from "@/components/MasterDetail.vue";
import ItemCard from "@/components/ItemCard.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { useSessionStore } from "@/stores/session";
import type { Processor } from "@/types/processor";

const sessionStore = useSessionStore();
const processors = ref<Processor[]>([]);
const selectedId = ref<number | null>(null);
const loading = ref(false);

const selected = computed(() => processors.value.find((p) => p.id === selectedId.value) ?? null);

async function loadProcessors() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try { processors.value = await fetchProcessors(token); }
  catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { loading.value = false; }
}

onMounted(loadProcessors);
</script>

<template>
  <div v-loading="loading">
    <MasterDetail :has-selection="selected !== null" empty-title="选择一个处理器" empty-description="从左侧列表选择处理器以查看详情。">
      <template #list>
        <div class="list-header">
          <span class="list-title">处理器 ({{ processors.length }})</span>
          <el-button text size="small" @click="loadProcessors">刷新</el-button>
        </div>
        <ItemCard v-for="p in processors" :key="p.id" :selected="selectedId === p.id" @click="selectedId = p.id">
          <div class="item-row">
            <span class="status-dot" :class="{ 'status-dot--online': p.status === 'online' }" />
            <div>
              <div class="item-title">{{ p.name }}</div>
              <div class="item-meta">{{ p.taskType }} · {{ p.status === 'online' ? '在线' : '离线' }}</div>
            </div>
          </div>
        </ItemCard>
        <div v-if="processors.length === 0" class="list-empty">暂无已注册的处理器</div>
      </template>

      <template #detail>
        <DetailPanel v-if="selected">
          <template #header>
            <div class="detail-head-row">
              <span class="status-dot status-dot--lg" :class="{ 'status-dot--online': selected.status === 'online' }" />
              <div>
                <h3 class="detail-title">{{ selected.name }}</h3>
                <StatusBadge :label="selected.status === 'online' ? '在线' : '离线'" :tone="selected.status === 'online' ? 'success' : 'muted'" />
              </div>
            </div>
          </template>

          <div class="detail-section">
            <h5 class="section-title">基本信息</h5>
            <div class="info-grid">
              <div><label>任务类型</label><span>{{ selected.taskType }}</span></div>
              <div><label>端点地址</label><span class="mono">{{ selected.endpointUrl }}</span></div>
              <div><label>注册时间</label><span>{{ selected.registeredAt }}</span></div>
              <div><label>最后心跳</label><span>{{ selected.lastHeartbeatAt }}</span></div>
            </div>
          </div>

          <div v-if="selected.description" class="detail-section">
            <h5 class="section-title">描述</h5>
            <p class="detail-desc">{{ selected.description }}</p>
          </div>
        </DetailPanel>
      </template>
    </MasterDetail>
  </div>
</template>

<style scoped>
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-3); }
.list-title { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.list-empty { padding: var(--sp-6); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm); }
.item-row { display: flex; align-items: center; gap: var(--sp-2); }
.item-title { font-weight: var(--weight-medium); font-size: var(--text-sm); color: var(--text-primary); }
.item-meta { font-size: var(--text-xs); color: var(--text-tertiary); margin-top: 2px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-tertiary); flex-shrink: 0; }
.status-dot--online { background: var(--success); }
.status-dot--lg { width: 12px; height: 12px; }
.detail-head-row { display: flex; align-items: center; gap: var(--sp-3); }
.detail-head-row > div { display: flex; flex-direction: column; gap: var(--sp-2); }
.detail-title { margin: 0; font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.detail-section { margin-bottom: var(--sp-5); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.info-grid div { display: flex; flex-direction: column; gap: 2px; }
.info-grid label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: var(--weight-medium); }
.info-grid span { font-size: var(--text-sm); color: var(--text-primary); }
.mono { font-family: var(--font-mono); font-size: var(--text-xs); }
.detail-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: var(--leading-relaxed); margin: 0; }
</style>
