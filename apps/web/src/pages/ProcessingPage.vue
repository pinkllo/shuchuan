<script setup lang="ts">
import { ref, onMounted } from 'vue'
import OverviewMetric from '@/components/OverviewMetric.vue'
import StatusPill from '@/components/StatusPill.vue'
import TaskCreateDialog from '@/components/TaskCreateDialog.vue'
import TaskLogDrawer from '@/components/TaskLogDrawer.vue'
import { useTaskStore, taskStatusLabels, taskStatusTones, type TaskItem } from '@/stores/taskStore'
import { usePermission } from '@/composables/usePermission'
import { useCapabilityStore, type Capability } from '@/stores/capabilityStore'
import { ElMessage } from 'element-plus'

const taskStore = useTaskStore()
const capabilityStore = useCapabilityStore()
const { can } = usePermission()

const activeTab = ref('tasks')
const showCreate = ref(false)
const showLog = ref(false)
const currentTask = ref<TaskItem | null>(null)
const filterType = ref('')

onMounted(() => {
  taskStore.initSimulations()
})

function openLog(task: TaskItem) {
  currentTask.value = task
  showLog.value = true
}

function filteredTasks() {
  if (!filterType.value) return taskStore.items
  return taskStore.items.filter(i => i.type === filterType.value)
}



/* ── 能力管理 ── */

const adapterModes = [
  { mode: 'SDK 接入', icon: '📦', fit: '适合可整理成 Python 库的项目', benefit: '调用链最短，日志最好打通' },
  { mode: 'CLI / 容器接入', icon: '🐳', fit: '适合当前大部分历史个人项目', benefit: '改造最少，环境隔离最清晰' },
  { mode: 'HTTP 服务接入', icon: '🌐', fit: '适合已独立部署的成熟能力', benefit: '边界清晰，支持异地部署' }
]

const showConfig = ref(false)
const configItem = ref<Capability | null>(null)

function openConfig(cap: Capability) {
  if (!cap.configurable) {
    ElMessage.info(`「${cap.name}」尚未接入，暂无法配置`)
    return
  }
  configItem.value = cap
  showConfig.value = true
}

function handleTest() {
  ElMessage.success('测试调用成功（模拟）')
  showConfig.value = false
}


</script>

<template>
  <div class="page-grid">
    <!-- 统计指标 -->
    <section class="metric-grid">
      <OverviewMetric
        label="累计产出样本"
        :value="taskStore.totalSamples.toLocaleString()"
        note="所有已完成任务的样本总量。"
        tone="jade"
      />
      <OverviewMetric
        label="平均通过率"
        :value="`${taskStore.avgPassRate}%`"
        note="已完成任务的平均质检通过率。"
        tone="amber"
      />
      <OverviewMetric
        label="执行中任务"
        :value="String(taskStore.runningCount)"
        :note="`另有 ${taskStore.completedCount} 个已完成。`"
        tone="slate"
      />
    </section>



    <!-- Tab 切换：任务中心 / 能力管理 -->
    <section class="surface-card">
      <el-tabs v-model="activeTab">
        <!-- ════ 任务中心 ════ -->
        <el-tab-pane label="任务中心" name="tasks">
          <div class="card-head">
            <div>
              <h3>所有任务</h3>
              <p>清洗、切分、指令生成、拆书、病句修改等处理任务统一管理。</p>
            </div>
            <div class="head-actions">
              <el-select v-model="filterType" placeholder="按能力筛选" clearable style="width:150px">
                <el-option v-for="cap in capabilityStore.capabilities" :key="cap.id" :label="cap.name" :value="cap.id" />
              </el-select>
              <el-button v-if="can('task.create')" type="primary" @click="showCreate = true">注册处理任务</el-button>
            </div>
          </div>

          <el-table :data="filteredTasks()" stripe>
            <el-table-column prop="id" label="编号" width="100" />
            <el-table-column label="任务" min-width="180">
              <template #default="{ row }">
                <el-button type="primary" link @click="openLog(row)">{{ row.name }}</el-button>
              </template>
            </el-table-column>
            <el-table-column label="处理能力" width="110">
              <template #default="{ row }">
                <el-tag size="small" type="info">{{ capabilityStore.capabilities.find(c => c.id === row.type)?.name || row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dataset" label="数据集" min-width="140" />
            <el-table-column label="进度" width="160">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress"
                  :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : undefined"
                  :stroke-width="8"
                />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <StatusPill :label="taskStatusLabels[row.status as keyof typeof taskStatusLabels]" :tone="taskStatusTones[row.status as keyof typeof taskStatusTones] as any" />
              </template>
            </el-table-column>
            <el-table-column label="产出" width="100">
              <template #default="{ row }">
                <span v-if="row.result">{{ row.result.sampleCount.toLocaleString() }} 条</span>
                <span v-else style="color:var(--text-muted)">—</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openLog(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ════ 能力管理 ════ -->
        <el-tab-pane label="能力管理" name="capabilities">
          <!-- 接入方式 -->
          <div class="card-head">
            <div>
              <h3>接入方式</h3>
              <p>平台支持三种方式接入外部数据处理能力。</p>
            </div>
          </div>
          <div class="three-col" style="margin-bottom:28px">
            <article v-for="item in adapterModes" :key="item.mode" class="flow-card">
              <p>{{ item.icon }} {{ item.mode }}</p>
              <strong>{{ item.fit }}</strong>
              <small>{{ item.benefit }}</small>
            </article>
          </div>

          <!-- 能力清单 -->
          <div class="card-head">
            <div>
              <h3>已注册能力</h3>
              <p>当前系统已注册或待接入的数据处理能力。</p>
            </div>
          </div>
          <div class="cap-grid" style="margin-bottom:28px">
            <article v-for="cap in capabilityStore.capabilities" :key="cap.id" class="cap-card">
              <div class="cap-header">
                <div>
                  <h4>{{ cap.name }}</h4>
                </div>
                <StatusPill :label="cap.status" :tone="cap.tone" />
              </div>
              <p class="cap-desc">{{ cap.description }}</p>
              <div class="cap-footer">
                <el-tag size="small" type="info">{{ cap.adapter }}</el-tag>
                <el-button
                  v-if="can('integration.configure')"
                  :type="cap.configurable ? 'primary' : 'info'"
                  size="small" plain
                  @click="openConfig(cap)"
                >
                  {{ cap.configurable ? '配置 / 测试' : '待接入' }}
                </el-button>
              </div>
            </article>
          </div>


        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- 配置对话框 -->
    <el-dialog v-model="showConfig" :title="`配置 — ${configItem?.name ?? ''}`" width="500px" destroy-on-close>
      <template v-if="configItem">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="能力名称">{{ configItem.name }}</el-descriptions-item>
          <el-descriptions-item label="接入方式">{{ configItem.adapter }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <StatusPill :label="configItem.status" :tone="configItem.tone" />
          </el-descriptions-item>
        </el-descriptions>
        <el-alert
          title="该能力已通过 SDK 成功接入，可在任务中心直接创建对应类型的任务来调用。"
          type="success" show-icon :closable="false" style="margin-top:16px"
        />
      </template>
      <template #footer>
        <el-button @click="showConfig = false">关闭</el-button>
        <el-button type="primary" @click="handleTest">发起测试调用</el-button>
      </template>
    </el-dialog>

    <TaskCreateDialog v-model:visible="showCreate" />
    <TaskLogDrawer v-model:visible="showLog" :task="currentTask" />
  </div>
</template>

<style scoped>
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.cap-grid {
  display: grid;
  gap: 14px;
}
.cap-card {
  padding: 22px;
  border-radius: 20px;
  background: var(--surface-strong);
  border: 1px solid var(--border-soft);
  transition: transform 180ms ease, box-shadow 180ms ease;
}
.cap-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(14, 53, 65, 0.1);
}
.cap-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.cap-header h4 {
  margin: 0;
  font-size: 18px;
}
.cap-owner {
  font-size: 13px;
  color: var(--text-muted);
}
.cap-desc {
  margin: 12px 0;
  line-height: 1.7;
  color: var(--text-soft);
}
.cap-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
