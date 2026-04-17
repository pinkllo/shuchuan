<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchAuditLogs, fetchPendingRegistrations } from "@/api/admin";
import { fetchDeliveries } from "@/api/deliveries";
import { getErrorMessage } from "@/api/http";
import KanbanBoard from "@/components/KanbanBoard.vue";
import KanbanColumn from "@/components/KanbanColumn.vue";
import KanbanCard from "@/components/KanbanCard.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import ProgressBar from "@/components/ProgressBar.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { useTaskStore } from "@/stores/taskStore";
import { demandStatusLabels } from "@/types/demand";
import type { DeliveryItem } from "@/types/delivery";
import { taskStatusLabels, formatTaskType } from "@/types/task";

const router = useRouter();
const sessionStore = useSessionStore();
const permission = usePermission();
const catalogStore = useCatalogStore();
const demandStore = useDemandStore();
const taskStore = useTaskStore();

const pendingCount = ref(0);
const auditCount = ref(0);
const deliveries = ref<DeliveryItem[]>([]);
const loading = ref(false);

// ── Computed data for kanban ──

const pendingDemands = computed(() => demandStore.items.filter((d) => d.status === "pending_approval"));
const activeDemands = computed(() => demandStore.items.filter((d) => d.status === "approved" || d.status === "data_uploaded"));
const recentDemands = computed(() => demandStore.items.filter((d) => d.status === "delivered" || d.status === "rejected").slice(0, 5));

const draftCatalogs = computed(() => catalogStore.items.filter((c) => c.status === "draft"));
const publishedCatalogs = computed(() => catalogStore.items.filter((c) => c.status === "published").slice(0, 5));

const runningTasks = computed(() => taskStore.items.filter((t) => t.status === "running" || t.status === "queued"));
const completedTasks = computed(() => taskStore.items.filter((t) => t.status === "completed").slice(0, 5));

// ── Load ──

async function loadDashboard() {
  const token = sessionStore.accessToken;
  if (!token) return;

  // Aggregator goes straight to workbench
  if (permission.isAggregator.value) {
    await router.replace("/workbench");
    return;
  }

  loading.value = true;
  try {
    if (permission.isAdmin.value) {
      const [registrations, logs] = await Promise.all([
        fetchPendingRegistrations(token),
        fetchAuditLogs(token)
      ]);
      pendingCount.value = registrations.length;
      auditCount.value = logs.length;
      return;
    }
    if (permission.isConsumer.value) {
      deliveries.value = await fetchDeliveries(token);
      return;
    }
    const jobs: Promise<unknown>[] = [demandStore.loadAll(token)];
    if (permission.isProvider.value) {
      jobs.push(catalogStore.loadMine(token));
    }
    await Promise.all(jobs);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function navigateTo(path: string) {
  router.push(path);
}

onMounted(loadDashboard);
</script>

<template>
  <div class="space-y-6" v-loading="loading">
    <!-- ── Provider Dashboard ── -->
    <template v-if="permission.isProvider.value">
      <h2 class="text-[18px] font-semibold text-gray-900 tracking-tight mb-4">工作看板</h2>
      <KanbanBoard>
        <KanbanColumn title="待处理" :count="pendingDemands.length">
          <KanbanCard v-for="d in pendingDemands" :key="d.id" @click="navigateTo('/demands')">
            <strong>{{ d.title }}</strong>
            <small>需求 #{{ d.id }} · {{ demandStatusLabels[d.status] }}</small>
          </KanbanCard>
          <div v-if="pendingDemands.length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-sm text-gray-400">暂无待处理需求</div>
        </KanbanColumn>
        <KanbanColumn title="进行中" :count="draftCatalogs.length">
          <KanbanCard v-for="c in draftCatalogs" :key="c.id" @click="navigateTo('/catalogs')">
            <strong>{{ c.name }} {{ c.version }}</strong>
            <small>草稿 · {{ c.assetCount ?? 0 }} 个文件</small>
          </KanbanCard>
          <div v-if="draftCatalogs.length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-sm text-gray-400">暂无草稿目录</div>
        </KanbanColumn>
        <KanbanColumn title="近期完成" :count="recentDemands.length + publishedCatalogs.length">
          <KanbanCard v-for="d in recentDemands" :key="`d-${d.id}`">
            <strong>{{ d.title }}</strong>
            <small>需求 #{{ d.id }} · {{ demandStatusLabels[d.status] }}</small>
          </KanbanCard>
          <KanbanCard v-for="c in publishedCatalogs" :key="`c-${c.id}`">
            <strong>{{ c.name }} {{ c.version }}</strong>
            <small>已发布</small>
          </KanbanCard>
        </KanbanColumn>
      </KanbanBoard>
    </template>

    <!-- ── Aggregator Dashboard ── -->
    <template v-else-if="permission.isAggregator.value">
      <h2 class="text-[18px] font-semibold text-gray-900 tracking-tight mb-4">工作看板</h2>
      <KanbanBoard>
        <KanbanColumn title="待处理" :count="pendingDemands.length + activeDemands.length">
          <KanbanCard v-for="d in pendingDemands" :key="d.id" @click="navigateTo('/demands')">
            <strong>{{ d.title }}</strong>
            <small>需求 #{{ d.id }} · 等待审批</small>
          </KanbanCard>
          <KanbanCard v-for="d in activeDemands" :key="`a-${d.id}`" @click="navigateTo('/demands')">
            <strong>{{ d.title }}</strong>
            <small>需求 #{{ d.id }} · 可创建任务</small>
          </KanbanCard>
          <div v-if="pendingDemands.length + activeDemands.length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-sm text-gray-400">暂无待处理事项</div>
        </KanbanColumn>
        <KanbanColumn title="处理中" :count="runningTasks.length">
          <KanbanCard v-for="t in runningTasks" :key="t.id" @click="navigateTo('/processing')">
            <strong>{{ formatTaskType(t.taskType) }} #{{ t.id }}</strong>
            <small>{{ t.processorName ?? '手动' }} · {{ taskStatusLabels[t.status] }}</small>
            <ProgressBar v-if="t.status === 'running'" :value="t.progress" style="margin-top: 6px" />
          </KanbanCard>
          <div v-if="runningTasks.length === 0" class="flex flex-col items-center justify-center py-10 px-4 text-sm text-gray-400">暂无运行中的任务</div>
        </KanbanColumn>
        <KanbanColumn title="近期完成" :count="completedTasks.length">
          <KanbanCard v-for="t in completedTasks" :key="t.id" @click="navigateTo('/processing')">
            <strong>{{ formatTaskType(t.taskType) }} #{{ t.id }}</strong>
            <small>{{ t.note ?? '已完成' }}</small>
          </KanbanCard>
        </KanbanColumn>
      </KanbanBoard>
    </template>

    <!-- ── Admin Dashboard ── -->
    <template v-else-if="permission.isAdmin.value">
      <h2 class="text-[18px] font-semibold text-gray-900 tracking-tight mb-4">管理看板</h2>
      <KanbanBoard>
        <KanbanColumn title="待处理" :count="pendingCount">
          <KanbanCard @click="navigateTo('/admin/approvals')">
            <strong>{{ pendingCount }} 个注册待审核</strong>
            <small>点击前往审核页面</small>
          </KanbanCard>
        </KanbanColumn>
        <KanbanColumn title="系统状态">
          <KanbanCard>
            <strong>👥 平台用户</strong>
            <small>审计记录 {{ auditCount }} 条</small>
          </KanbanCard>
          <KanbanCard @click="navigateTo('/admin/processors')">
            <strong>🔧 处理器管理</strong>
            <small>查看已注册的外部处理服务</small>
          </KanbanCard>
        </KanbanColumn>
        <KanbanColumn title="快捷入口">
          <KanbanCard @click="navigateTo('/admin/logs')">
            <strong>📋 审计日志</strong>
            <small>查看关键操作记录</small>
          </KanbanCard>
          <KanbanCard @click="navigateTo('/admin/users')">
            <strong>👤 用户管理</strong>
            <small>管理平台账号</small>
          </KanbanCard>
        </KanbanColumn>
      </KanbanBoard>
    </template>

    <!-- ── Consumer Dashboard ── -->
    <template v-else-if="permission.isConsumer.value">
      <h2 class="text-[18px] font-semibold text-gray-900 tracking-tight mb-4">交付结果</h2>
      <section class="bg-white border border-gray-200 rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.04)] p-6 transition-all duration-200">
        <el-table :data="deliveries" style="width: 100%" class="[&_.el-table__header-wrapper_th]:!bg-gray-50 [&_.el-table__header-wrapper_th]:!text-gray-500 [&_.el-table__header-wrapper_th]:!font-medium [&_.el-table__header-wrapper_th]:!text-xs [&_.el-table__row]:!transition-colors [&_.el-table__row:hover>td]:!bg-gray-50">
          <el-table-column prop="demandTitle" label="需求标题" min-width="220" />
          <el-table-column prop="artifactFileName" label="文件名" min-width="200" />
          <el-table-column prop="sampleCount" label="样本数" width="110" />
          <el-table-column prop="deliveredAt" label="交付时间" width="180" />
          <el-table-column label="操作" width="100">
            <template #default>
              <el-button type="primary" text size="small">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </template>
  </div>
</template>
