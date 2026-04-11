<script setup lang="ts">
import { ref } from 'vue'
import StatusPill from '@/components/StatusPill.vue'
import DemandFormDialog from '@/components/DemandFormDialog.vue'
import ApprovalDialog from '@/components/ApprovalDialog.vue'
import FileUploadDialog from '@/components/FileUploadDialog.vue'
import { useDemandStore, demandStatusLabels, demandStatusTones, type DemandItem } from '@/stores/demandStore'
import { usePermission } from '@/composables/usePermission'
import { ElMessage } from 'element-plus'

const demandStore = useDemandStore()
const { can, isConsumer } = usePermission()

const showDemandForm = ref(false)
const showApproval = ref(false)
const showUpload = ref(false)
const showDetail = ref(false)

const currentDemand = ref<DemandItem | null>(null)
const filterStatus = ref('')

const filteredItems = ref(demandStore.items)

function doFilter() {
  if (!filterStatus.value) {
    filteredItems.value = demandStore.items
  } else {
    filteredItems.value = demandStore.items.filter(i => i.status === filterStatus.value)
  }
}

function openApproval(item: DemandItem) {
  currentDemand.value = item
  showApproval.value = true
}

function openUpload(item: DemandItem) {
  currentDemand.value = item
  showUpload.value = true
}

function openDetail(item: DemandItem) {
  currentDemand.value = item
  showDetail.value = true
}

function handleMarkDelivered(item: DemandItem) {
  demandStore.markDelivered(item.id)
  ElMessage.success('已标记为已交付')
}

function handleDownload() {
  ElMessage.info('下载功能将在对接后端后可用')
}
</script>

<template>
  <div class="page-grid">
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>需求协同</h3>
          <p>需求发起、审批、数据上传与交付的全流程管理。</p>
        </div>
        <div class="head-actions">
          <el-select v-model="filterStatus" placeholder="按状态筛选" clearable style="width:160px" @change="doFilter">
            <el-option v-for="(label, key) in demandStatusLabels" :key="key" :label="label" :value="key" />
          </el-select>
          <el-button v-if="can('demand.create')" type="primary" @click="showDemandForm = true">发起需求</el-button>
        </div>
      </div>

      <el-table :data="filteredItems" stripe>
        <el-table-column prop="id" label="编号" width="100" />
        <el-table-column label="需求标题" min-width="200">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">{{ row.title }}</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="requester" label="发起方" width="130" />
        <el-table-column prop="provider" label="提供方" width="130" />
        <el-table-column prop="catalogName" label="关联目录" min-width="150" />
        <el-table-column label="附件" width="80">
          <template #default="{ row }">
            <span v-if="row.files.length">{{ row.files.length }} 个</span>
            <span v-else style="color:var(--text-muted)">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusPill :label="demandStatusLabels[row.status as keyof typeof demandStatusLabels]" :tone="demandStatusTones[row.status as keyof typeof demandStatusTones] as any" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <!-- 提供者：审批 / 上传 -->
            <el-button v-if="can('demand.approve') && row.status === 'pending'" type="primary" link size="small" @click="openApproval(row)">审批</el-button>
            <el-button v-if="can('demand.upload') && row.status === 'approved'" type="success" link size="small" @click="openUpload(row)">上传数据</el-button>
            <!-- 汇聚者：标记交付 -->
            <el-button v-if="can('task.manage') && row.status === 'processing'" type="success" link size="small" @click="handleMarkDelivered(row)">标记交付</el-button>
            <!-- 使用者：下载 -->
            <el-button v-if="can('delivery.download') && row.status === 'delivered'" type="primary" link size="small" @click="handleDownload">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section>
      <article class="surface-card">
        <div class="card-head">
          <div>
            <h3>当前统计</h3>
            <p>需求各状态的分布概况。</p>
          </div>
        </div>
        <div class="stat-list">
          <div class="stat-row">
            <span>待审批</span>
            <strong class="stat-warn">{{ demandStore.pendingCount }}</strong>
          </div>
          <div class="stat-row">
            <span>进行中</span>
            <strong class="stat-info">{{ demandStore.activeCount }}</strong>
          </div>
          <div class="stat-row">
            <span>已交付</span>
            <strong class="stat-good">{{ demandStore.deliveredCount }}</strong>
          </div>
          <div class="stat-row">
            <span>总计</span>
            <strong>{{ demandStore.items.length }}</strong>
          </div>
        </div>
      </article>
    </section>

    <!-- 需求详情抽屉 -->
    <el-drawer v-model="showDetail" :title="`需求详情 — ${currentDemand?.id ?? ''}`" size="500px" direction="rtl">
      <template v-if="currentDemand">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="需求标题">{{ currentDemand.title }}</el-descriptions-item>
          <el-descriptions-item label="发起方">{{ currentDemand.requester }}</el-descriptions-item>
          <el-descriptions-item label="提供方">{{ currentDemand.provider }}</el-descriptions-item>
          <el-descriptions-item label="关联目录">{{ currentDemand.catalogName }}</el-descriptions-item>
          <el-descriptions-item label="用途说明">{{ currentDemand.purpose }}</el-descriptions-item>
          <el-descriptions-item label="交付计划">{{ currentDemand.deliveryPlan || '—' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusPill :label="demandStatusLabels[currentDemand.status]" :tone="demandStatusTones[currentDemand.status] as any" />
          </el-descriptions-item>
          <el-descriptions-item v-if="currentDemand.approvalNote" label="审批意见">{{ currentDemand.approvalNote }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentDemand.createdAt }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentDemand.updatedAt }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentDemand.files.length" style="margin-top:20px">
          <h4 style="margin:0 0 10px">已上传文件</h4>
          <div v-for="f in currentDemand.files" :key="f.name" class="file-row">
            <span>📄 {{ f.name }}</span>
            <span class="file-meta">{{ f.size }} · {{ f.uploadedAt }}</span>
          </div>
        </div>
      </template>
    </el-drawer>

    <DemandFormDialog v-model:visible="showDemandForm" />
    <ApprovalDialog v-model:visible="showApproval" :demand="currentDemand" />
    <FileUploadDialog v-model:visible="showUpload" :demand="currentDemand" />
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.stat-list {
  display: grid;
  gap: 10px;
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-radius: 14px;
  background: var(--surface-strong);
  border: 1px solid var(--border-soft);
}
.stat-row span {
  color: var(--text-soft);
}
.stat-row strong {
  font-size: 24px;
}
.stat-warn { color: #c77b1a; }
.stat-info { color: #125c7a; }
.stat-good { color: #14674f; }
.file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(239, 247, 245, 0.5);
  border: 1px solid var(--border-soft);
  margin-bottom: 6px;
  font-size: 14px;
}
.file-meta {
  color: var(--text-muted);
  font-size: 13px;
}
</style>
