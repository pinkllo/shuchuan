<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { type TaskItem, taskTypeLabels, taskStatusLabels } from '@/stores/taskStore'

const props = defineProps<{ visible: boolean; task: TaskItem | null }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const logEnd = ref<HTMLElement>()

const configEntries = computed(() => {
  if (!props.task) return []
  return Object.entries(props.task.config).map(([k, v]) => ({ key: k, value: v }))
})

watch(() => props.task?.logs.length, async () => {
  await nextTick()
  logEnd.value?.scrollIntoView({ behavior: 'smooth' })
})

function handleDownload() {
  const blob = new Blob([JSON.stringify(props.task, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.task?.id ?? 'task'}_result.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :title="`任务详情 — ${task?.id ?? ''}`"
    size="520px"
    direction="rtl"
  >
    <template v-if="task">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="任务名称">{{ task.name }}</el-descriptions-item>
        <el-descriptions-item label="任务类型">
          <el-tag size="small">{{ taskTypeLabels[task.type] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据集">{{ task.dataset }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="task.status === 'completed' ? 'success' : task.status === 'failed' ? 'danger' : task.status === 'running' ? '' : 'warning'" size="small">
            {{ taskStatusLabels[task.status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ task.createdAt }}</el-descriptions-item>
      </el-descriptions>

      <!-- 进度 -->
      <div class="drawer-section">
        <h4>执行进度</h4>
        <el-progress
          :percentage="task.progress"
          :status="task.status === 'completed' ? 'success' : task.status === 'failed' ? 'exception' : undefined"
          :stroke-width="12"
          style="margin-top:8px"
        />
      </div>

      <!-- 配置参数 -->
      <div v-if="configEntries.length" class="drawer-section">
        <h4>配置参数</h4>
        <div class="config-grid">
          <div v-for="entry in configEntries" :key="entry.key" class="config-item">
            <span class="config-label">{{ entry.key }}</span>
            <span>{{ entry.value }}</span>
          </div>
        </div>
      </div>

      <!-- 结果 -->
      <div v-if="task.result" class="drawer-section">
        <h4>执行结果</h4>
        <div class="result-grid">
          <div class="result-card">
            <span>产出样本</span>
            <strong>{{ task.result.sampleCount.toLocaleString() }}</strong>
          </div>
          <div class="result-card">
            <span>通过率</span>
            <strong>{{ task.result.passRate }}%</strong>
          </div>
          <div class="result-card">
            <span>输出格式</span>
            <strong>{{ task.result.outputFormat }}</strong>
          </div>
        </div>
        <el-button type="primary" style="margin-top:12px;width:100%" @click="handleDownload">
          下载结果文件
        </el-button>
      </div>

      <!-- 日志 -->
      <div class="drawer-section">
        <h4>执行日志</h4>
        <div class="log-box">
          <p v-for="(line, i) in task.logs" :key="i" class="log-line">{{ line }}</p>
          <div ref="logEnd" />
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.drawer-section {
  margin-top: 24px;
}
.drawer-section h4 {
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--text-main);
}
.config-grid {
  display: grid;
  gap: 6px;
}
.config-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(239, 247, 245, 0.5);
  font-size: 13px;
}
.config-label {
  color: var(--text-muted);
}
.result-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.result-card {
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(150deg, #f4fcf8, #dff2e8);
  text-align: center;
}
.result-card span {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.result-card strong {
  font-size: 20px;
  color: #0f4d44;
}
.log-box {
  max-height: 280px;
  overflow-y: auto;
  padding: 14px;
  border-radius: 14px;
  background: #1a2332;
  color: #a8d8c8;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.8;
}
.log-line {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
