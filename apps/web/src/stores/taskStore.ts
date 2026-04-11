import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type TaskType = 'clean' | 'split' | 'instruction' | 'quality_check' | 'book_split' | 'grammar_fix'
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface TaskResult {
  sampleCount: number
  passRate: number
  outputFormat: string
}

export interface TaskItem {
  id: string
  name: string
  type: TaskType
  dataset: string
  demandId: string
  owner: string
  status: TaskStatus
  progress: number
  config: Record<string, string>
  logs: string[]
  result: TaskResult | null
  createdAt: string
  updatedAt: string
}

export const taskTypeLabels: Record<TaskType, string> = {
  clean: '数据清洗',
  split: '样本切分',
  instruction: '指令生成',
  quality_check: '质量检查',
  book_split: '拆书',
  grammar_fix: '病句修改'
}

export const taskStatusLabels: Record<TaskStatus, string> = {
  pending: '排队中',
  running: '执行中',
  completed: '已完成',
  failed: '失败'
}

export const taskStatusTones: Record<TaskStatus, string> = {
  pending: 'warn',
  running: 'info',
  completed: 'good',
  failed: 'danger'
}

let nextId = 4
const timers = new Map<string, number>()

export const useTaskStore = defineStore('task', () => {
  const items = ref<TaskItem[]>([
    {
      id: 'TSK-001',
      name: '教育问答指令生成',
      type: 'instruction',
      dataset: '课程论坛问答集',
      demandId: 'DEM-003',
      owner: '俊才',
      status: 'running',
      progress: 72,
      config: { model: 'Qwen-2.5-72B', promptTemplate: '标准问答模板', batchSize: '32' },
      logs: [
        '[04-08 10:23] 任务启动，加载数据集...',
        '[04-08 10:24] 数据集加载完成，共 3,200 条',
        '[04-08 10:25] 开始指令生成，使用模型 Qwen-2.5-72B',
        '[04-08 14:30] 已完成 2,304 / 3,200 条 (72%)'
      ],
      result: null,
      createdAt: '2026-04-08',
      updatedAt: '2026-04-10'
    },
    {
      id: 'TSK-002',
      name: '病句修改样本构造',
      type: 'grammar_fix',
      dataset: '行业术语词表',
      demandId: 'DEM-002',
      owner: '张硕',
      status: 'pending',
      progress: 0,
      config: { errorTypes: '术语误用,语序错误,搭配不当', sampleRatio: '1:3' },
      logs: ['[04-09 09:00] 任务已创建，等待数据就绪...'],
      result: null,
      createdAt: '2026-04-09',
      updatedAt: '2026-04-09'
    },
    {
      id: 'TSK-003',
      name: '拆书实验批次',
      type: 'book_split',
      dataset: '教材样本集',
      demandId: '',
      owner: '研一同学',
      status: 'completed',
      progress: 100,
      config: { splitStrategy: '按章节', minLength: '500', maxLength: '3000' },
      logs: [
        '[04-06 08:00] 任务启动',
        '[04-06 08:15] 拆分完成，共产出 482 个片段',
        '[04-06 08:16] 质检通过率 91.3%'
      ],
      result: { sampleCount: 482, passRate: 91.3, outputFormat: 'JSONL' },
      createdAt: '2026-04-06',
      updatedAt: '2026-04-06'
    }
  ])

  const runningCount   = computed(() => items.value.filter(i => i.status === 'running').length)
  const completedCount = computed(() => items.value.filter(i => i.status === 'completed').length)
  const totalSamples   = computed(() => items.value.reduce((s, i) => s + (i.result?.sampleCount ?? 0), 0))
  const avgPassRate    = computed(() => {
    const done = items.value.filter(i => i.result)
    if (!done.length) return 0
    return Math.round(done.reduce((s, i) => s + (i.result?.passRate ?? 0), 0) / done.length * 10) / 10
  })

  function now() {
    const d = new Date()
    return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  function addTask(data: {
    name: string; type: TaskType; dataset: string; demandId: string; owner: string; config: Record<string, string>
  }) {
    const id = `TSK-${String(nextId++).padStart(3, '0')}`
    const task: TaskItem = {
      ...data, id,
      status: 'running',
      progress: 0,
      logs: [`[${now()}] 任务已创建并开始执行...`],
      result: null,
      createdAt: new Date().toISOString().slice(0, 10),
      updatedAt: new Date().toISOString().slice(0, 10)
    }
    items.value.unshift(task)
    startSimulation(id)
    return id
  }

  function startSimulation(id: string) {
    if (timers.has(id)) return
    const timer = window.setInterval(() => {
      const task = items.value.find(i => i.id === id)
      if (!task || task.status !== 'running') {
        clearInterval(timer)
        timers.delete(id)
        return
      }
      const step = Math.floor(Math.random() * 8) + 3
      task.progress = Math.min(task.progress + step, 100)
      task.logs.push(`[${now()}] 进度更新：${task.progress}%`)
      task.updatedAt = new Date().toISOString().slice(0, 10)
      if (task.progress >= 100) {
        task.status = 'completed'
        task.result = {
          sampleCount: Math.floor(Math.random() * 3000) + 500,
          passRate: Math.round((85 + Math.random() * 12) * 10) / 10,
          outputFormat: 'JSONL'
        }
        task.logs.push(`[${now()}] ✅ 任务完成！产出 ${task.result.sampleCount} 条，通过率 ${task.result.passRate}%`)
        clearInterval(timer)
        timers.delete(id)
      }
    }, 3000)
    timers.set(id, timer)
  }

  function initSimulations() {
    items.value.filter(i => i.status === 'running').forEach(i => startSimulation(i.id))
  }

  return { items, runningCount, completedCount, totalSamples, avgPassRate, addTask, initSimulations }
})
