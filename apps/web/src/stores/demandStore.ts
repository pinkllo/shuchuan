import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DemandStatus = 'pending' | 'approved' | 'rejected' | 'uploading' | 'processing' | 'delivered'

export interface UploadedFile {
  name: string
  size: string
  uploadedAt: string
}

export interface DemandItem {
  id: string
  title: string
  requester: string
  provider: string
  catalogId: string
  catalogName: string
  purpose: string
  deliveryPlan: string
  status: DemandStatus
  approvalNote: string
  files: UploadedFile[]
  createdAt: string
  updatedAt: string
}

export const demandStatusLabels: Record<DemandStatus, string> = {
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
  uploading: '数据上传中',
  processing: '处理中',
  delivered: '已交付'
}

export const demandStatusTones: Record<DemandStatus, string> = {
  pending: 'warn',
  approved: 'info',
  rejected: 'danger',
  uploading: 'info',
  processing: 'info',
  delivered: 'good'
}

let nextId = 4

export const useDemandStore = defineStore('demand', () => {
  const items = ref<DemandItem[]>([
    {
      id: 'DEM-001',
      title: '面向教育场景的问答清洗需求',
      requester: '数据汇聚者组',
      provider: '数据提供者 A',
      catalogId: 'CAT-001',
      catalogName: '课程论坛问答集',
      purpose: '清洗后用于教育问答模型的微调训练，需要去除无效回复和敏感内容。',
      deliveryPlan: '2026 年 5 月底前完成',
      status: 'pending',
      approvalNote: '',
      files: [],
      createdAt: '2026-04-01',
      updatedAt: '2026-04-01'
    },
    {
      id: 'DEM-002',
      title: '病句修改训练样本补充',
      requester: '张硕',
      provider: '数据提供者 B',
      catalogId: 'CAT-002',
      catalogName: '行业术语词表',
      purpose: '构造包含术语误用的病句训练对，支持病句修改模型优化。',
      deliveryPlan: '持续滚动交付',
      status: 'approved',
      approvalNote: '同意提供，注意标注术语来源。',
      files: [
        { name: '术语词表_v2026.03.csv', size: '2.4 MB', uploadedAt: '2026-04-05' }
      ],
      createdAt: '2026-03-20',
      updatedAt: '2026-04-05'
    },
    {
      id: 'DEM-003',
      title: '指令生成训练集一期交付',
      requester: '俊才',
      provider: '数据提供者 C',
      catalogId: 'CAT-003',
      catalogName: '科研项目摘要',
      purpose: '基于科研摘要生成高质量问答指令对，用于通用对话模型增强。',
      deliveryPlan: '2026 年 4 月中旬',
      status: 'delivered',
      approvalNote: '已完成全部交付，质检通过率 94%。',
      files: [
        { name: '科研摘要_batch1.jsonl', size: '18.7 MB', uploadedAt: '2026-03-30' },
        { name: '科研摘要_batch2.jsonl', size: '12.3 MB', uploadedAt: '2026-04-02' }
      ],
      createdAt: '2026-02-28',
      updatedAt: '2026-04-08'
    }
  ])

  const pendingCount = computed(() => items.value.filter(i => i.status === 'pending').length)
  const activeCount  = computed(() => items.value.filter(i => !['rejected', 'delivered'].includes(i.status)).length)
  const deliveredCount = computed(() => items.value.filter(i => i.status === 'delivered').length)

  function addDemand(data: {
    title: string; requester: string; provider: string;
    catalogId: string; catalogName: string; purpose: string; deliveryPlan: string
  }) {
    const id = `DEM-${String(nextId++).padStart(3, '0')}`
    const now = new Date().toISOString().slice(0, 10)
    items.value.unshift({
      ...data, id,
      status: 'pending',
      approvalNote: '',
      files: [],
      createdAt: now,
      updatedAt: now
    })
    return id
  }

  function approveDemand(id: string, note: string) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.status = 'approved'
      item.approvalNote = note
      item.updatedAt = new Date().toISOString().slice(0, 10)
    }
  }

  function rejectDemand(id: string, note: string) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.status = 'rejected'
      item.approvalNote = note
      item.updatedAt = new Date().toISOString().slice(0, 10)
    }
  }

  function addFiles(id: string, files: UploadedFile[]) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.files.push(...files)
      if (item.status === 'approved') item.status = 'uploading'
      item.updatedAt = new Date().toISOString().slice(0, 10)
      setTimeout(() => {
        if (item.status === 'uploading') {
          item.status = 'processing'
          item.updatedAt = new Date().toISOString().slice(0, 10)
        }
      }, 2500)
    }
  }

  function markDelivered(id: string) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.status = 'delivered'
      item.updatedAt = new Date().toISOString().slice(0, 10)
    }
  }

  return { items, pendingCount, activeCount, deliveredCount, addDemand, approveDemand, rejectDemand, addFiles, markDelivered }
})
