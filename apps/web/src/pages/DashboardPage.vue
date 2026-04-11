<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import OverviewMetric from '@/components/OverviewMetric.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useCatalogStore } from '@/stores/catalogStore'
import { useDemandStore, demandStatusLabels, demandStatusTones } from '@/stores/demandStore'
import { useTaskStore, taskStatusLabels, taskStatusTones } from '@/stores/taskStore'
import { useCapabilityStore } from '@/stores/capabilityStore'
import { usePermission } from '@/composables/usePermission'

const router = useRouter()
const catalogStore = useCatalogStore()
const demandStore = useDemandStore()
const taskStore = useTaskStore()
const capabilityStore = useCapabilityStore()
const { isProvider, isAggregator, isConsumer } = usePermission()

onMounted(() => {
  taskStore.initSimulations()
})

function goTo(name: string) {
  router.push({ name })
}
</script>

<template>
  <div class="page-grid">
    <!-- 指标概览 -->
    <section class="metric-grid">
      <OverviewMetric
        label="数据目录"
        :value="String(catalogStore.totalCount)"
        :note="`其中 ${catalogStore.publishedCount} 个已发布，可供汇聚者申请使用。`"
        tone="jade"
      />
      <OverviewMetric
        label="协同需求"
        :value="String(demandStore.items.length)"
        :note="`${demandStore.pendingCount} 个待审批，${demandStore.deliveredCount} 个已交付。`"
        tone="amber"
      />
      <OverviewMetric
        label="处理任务"
        :value="String(taskStore.items.length)"
        :note="`${taskStore.runningCount} 个执行中，累计产出 ${taskStore.totalSamples.toLocaleString()} 条样本。`"
        tone="slate"
      />
    </section>

    <!-- 快捷操作 -->
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>快捷操作</h3>
          <p>根据你的角色，选择接下来要做的事。</p>
        </div>
      </div>
      <div class="quick-actions">
        <button v-if="isProvider" class="quick-btn quick-btn--jade" @click="goTo('catalogs')">
          <strong>📦 发布数据</strong>
          <span>发布可提供的数据集</span>
        </button>
        <button v-if="isProvider" class="quick-btn quick-btn--amber" @click="goTo('demands')">
          <strong>✅ 审批需求</strong>
          <span>查看并审批 {{ demandStore.pendingCount }} 个待处理需求</span>
        </button>
        <button v-if="isAggregator" class="quick-btn quick-btn--jade" @click="goTo('demands')">
          <strong>📋 发起需求</strong>
          <span>围绕已发布数据集提交数据需求</span>
        </button>
        <button v-if="isAggregator" class="quick-btn quick-btn--slate" @click="goTo('processing')">
          <strong>⚙️ 注册处理任务</strong>
          <span>选择处理能力，注册数据处理任务</span>
        </button>
        <button v-if="isConsumer" class="quick-btn quick-btn--jade" @click="goTo('demands')">
          <strong>📥 查看交付</strong>
          <span>查看 {{ demandStore.deliveredCount }} 个已交付数据集</span>
        </button>
        <button class="quick-btn quick-btn--muted" @click="goTo('integration')">
          <strong>🔌 能力接入</strong>
          <span>查看拆书、病句修改等能力接入状态</span>
        </button>
      </div>
    </section>

    <!-- 进行中的任务 -->
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>进行中的任务</h3>
          <p>跨角色协同的任务状态实时展示。</p>
        </div>
        <el-button type="primary" plain size="small" @click="goTo('processing')">查看全部</el-button>
      </div>

      <el-table :data="taskStore.items.slice(0, 5)" stripe>
        <el-table-column prop="id" label="编号" width="110" />
        <el-table-column prop="name" label="任务" min-width="180" />
        <el-table-column label="处理能力" width="110">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ capabilityStore.capabilities.find(c => c.id === row.type)?.name || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : undefined"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusPill :label="taskStatusLabels[row.status as keyof typeof taskStatusLabels]" :tone="taskStatusTones[row.status as keyof typeof taskStatusTones] as any" />
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 最近需求动态 -->
    <section class="surface-card">
      <div class="card-head">
        <div>
          <h3>最近需求动态</h3>
          <p>需求协同的最新状态变化。</p>
        </div>
        <el-button type="primary" plain size="small" @click="goTo('demands')">查看全部</el-button>
      </div>

      <el-table :data="demandStore.items.slice(0, 5)" stripe>
        <el-table-column prop="id" label="编号" width="110" />
        <el-table-column prop="title" label="需求" min-width="200" />
        <el-table-column prop="requester" label="发起方" width="130" />
        <el-table-column prop="catalogName" label="关联目录" min-width="150" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusPill :label="demandStatusLabels[row.status as keyof typeof demandStatusLabels]" :tone="demandStatusTones[row.status as keyof typeof demandStatusTones] as any" />
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="120" />
      </el-table>
    </section>
  </div>
</template>
