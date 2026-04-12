<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { fetchAuditLogs, fetchPendingRegistrations } from "@/api/admin";
import { fetchDeliveries } from "@/api/deliveries";
import { getErrorMessage } from "@/api/http";
import OverviewMetric from "@/components/OverviewMetric.vue";
import StatusPill from "@/components/StatusPill.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { useTaskStore } from "@/stores/taskStore";
import { roleLabels } from "@/types/auth";
import { demandStatusLabels, demandStatusTones } from "@/types/demand";
import type { DeliveryItem } from "@/types/delivery";
import { taskStatusLabels, taskStatusTones } from "@/types/task";

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

const metrics = computed(() => {
  if (permission.isAdmin.value) {
    return [
      { label: "待审核申请", value: String(pendingCount.value), note: "管理员需要处理的新申请数量。", tone: "amber" as const },
      { label: "审计记录", value: String(auditCount.value), note: "平台关键写操作和下载记录总数。", tone: "slate" as const },
      { label: "管理角色", value: roleLabels.admin, note: "管理员仅做审核、查看与审计。", tone: "jade" as const }
    ];
  }
  if (permission.isConsumer.value) {
    return [
      { label: "交付结果", value: String(deliveries.value.length), note: "当前可供下载的最终交付文件数量。", tone: "jade" as const },
      { label: "消费者角色", value: roleLabels.consumer, note: "仅查看和下载最终交付结果。", tone: "slate" as const }
    ];
  }
  return [
    { label: "数据目录", value: String(catalogStore.totalCount), note: "当前角色可见的数据目录数量。", tone: "jade" as const },
    { label: "协同需求", value: String(demandStore.items.length), note: "当前角色可见的需求数量。", tone: "amber" as const },
    { label: "处理任务", value: String(taskStore.items.length), note: "当前角色关联的处理任务数量。", tone: "slate" as const }
  ];
});

async function loadDashboard() {
  const token = sessionStore.accessToken;
  if (!token) {
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
    const jobs: Promise<unknown>[] = [
      demandStore.loadAll(token)
    ];
    if (permission.isProvider.value) {
      jobs.push(catalogStore.loadMine(token));
    }
    if (permission.isAggregator.value) {
      jobs.push(catalogStore.loadPublished(token), taskStore.loadAll(token));
    }
    await Promise.all(jobs);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function goTo(path: string) {
  router.push(path);
}

onMounted(loadDashboard);
</script>

<template>
  <div class="page-grid">
    <section class="metric-grid">
      <OverviewMetric
        v-for="item in metrics"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :note="item.note"
        :tone="item.tone"
      />
    </section>

    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>当前入口</h3>
          <p>根据当前角色进入对应的真实页面。</p>
        </div>
      </div>
      <div class="quick-actions">
        <button v-if="permission.isProvider" class="quick-btn quick-btn--jade" @click="goTo('/catalogs')">
          <strong>目录管理</strong>
          <span>发布目录、发布或归档目录，并查看归属需求。</span>
        </button>
        <button v-if="permission.isProvider" class="quick-btn quick-btn--amber" @click="goTo('/demands')">
          <strong>需求审批</strong>
          <span>审批汇聚者需求并上传原始文件。</span>
        </button>
        <button v-if="permission.isAggregator" class="quick-btn quick-btn--jade" @click="goTo('/demands')">
          <strong>发起需求</strong>
          <span>基于已发布目录发起真实数据需求。</span>
        </button>
        <button v-if="permission.isAggregator" class="quick-btn quick-btn--slate" @click="goTo('/processing')">
          <strong>任务中心</strong>
          <span>登记指令生成任务，推进状态并登记产物。</span>
        </button>
        <button v-if="permission.isConsumer" class="quick-btn quick-btn--jade" @click="goTo('/deliveries')">
          <strong>交付下载</strong>
          <span>下载最终交付文件，当前共 {{ deliveries.length }} 个。</span>
        </button>
        <button v-if="permission.isAdmin" class="quick-btn quick-btn--amber" @click="goTo('/admin/approvals')">
          <strong>注册审核</strong>
          <span>当前待审核 {{ pendingCount }} 个申请。</span>
        </button>
        <button v-if="permission.isAdmin" class="quick-btn quick-btn--slate" @click="goTo('/admin/logs')">
          <strong>审计日志</strong>
          <span>查看关键写操作和交付下载记录。</span>
        </button>
      </div>
    </section>

    <section v-if="permission.isAggregator || permission.isProvider" class="surface-card">
      <div class="card-head">
        <div>
          <h3>最近需求</h3>
          <p>真实接口返回的需求状态，不做自动推进。</p>
        </div>
      </div>
      <el-table :data="demandStore.items.slice(0, 5)" stripe v-loading="loading">
        <el-table-column prop="id" label="需求" width="90" />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusPill :label="demandStatusLabels[row.status]" :tone="demandStatusTones[row.status]" />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="180" />
      </el-table>
    </section>

    <section v-if="permission.isAggregator" class="surface-card">
      <div class="card-head">
        <div>
          <h3>最近任务</h3>
          <p>只展示当前汇聚者创建的任务。</p>
        </div>
      </div>
      <el-table :data="taskStore.items.slice(0, 5)" stripe v-loading="loading">
        <el-table-column prop="id" label="任务" width="90" />
        <el-table-column prop="taskType" label="类型" min-width="140" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusPill :label="taskStatusLabels[row.status]" :tone="taskStatusTones[row.status]" />
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="220" />
      </el-table>
    </section>

    <section v-if="permission.isConsumer" class="surface-card">
      <div class="card-head">
        <div>
          <h3>最近交付</h3>
          <p>消费者只看到最终可下载结果。</p>
        </div>
      </div>
      <el-table :data="deliveries.slice(0, 5)" stripe v-loading="loading">
        <el-table-column prop="demandId" label="需求" width="90" />
        <el-table-column prop="demandTitle" label="标题" min-width="220" />
        <el-table-column prop="artifactFileName" label="文件" min-width="220" />
        <el-table-column prop="sampleCount" label="样本数" width="110" />
      </el-table>
    </section>
  </div>
</template>
