import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type CatalogStatus = 'draft' | 'published' | 'archived'
export type Sensitivity = 'public' | 'internal' | 'sensitive'

export interface CatalogItem {
  id: string
  name: string
  provider: string
  type: string
  granularity: string
  version: string
  status: CatalogStatus
  fields: string
  scale: string
  sensitivity: Sensitivity
  description: string
  createdAt: string
}

export const sensitivityLabels: Record<Sensitivity, string> = {
  public: '公开',
  internal: '内部',
  sensitive: '敏感'
}

export const catalogStatusLabels: Record<CatalogStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档'
}

export const catalogStatusTones: Record<CatalogStatus, string> = {
  draft: 'warn',
  published: 'good',
  archived: 'info'
}

let nextId = 4

export const useCatalogStore = defineStore('catalog', () => {
  const items = ref<CatalogItem[]>([
    {
      id: 'CAT-001',
      name: '课程论坛问答集',
      provider: '数据提供者 A',
      type: '文本',
      granularity: '主题 / 帖子 / 回复',
      version: 'v2026.04',
      status: 'published',
      fields: '帖子标题、正文、回复内容、发布时间、用户标签',
      scale: '约 12,000 条问答对',
      sensitivity: 'internal',
      description: '来自高校课程论坛的问答数据，已做初步脱敏处理，可用于教育场景问答模型训练。',
      createdAt: '2026-03-28'
    },
    {
      id: 'CAT-002',
      name: '行业术语词表',
      provider: '数据提供者 B',
      type: '结构化表格',
      granularity: '术语 / 定义 / 来源',
      version: 'v2026.03',
      status: 'draft',
      fields: '术语名、英文名、定义、所属领域、来源文献',
      scale: '约 8,500 条',
      sensitivity: 'public',
      description: '多领域行业术语汇总表，包含术语定义及来源标注。',
      createdAt: '2026-03-15'
    },
    {
      id: 'CAT-003',
      name: '科研项目摘要',
      provider: '数据提供者 C',
      type: '文本',
      granularity: '项目 / 摘要 / 标签',
      version: 'v2026.02',
      status: 'published',
      fields: '项目编号、项目名称、摘要、关键词、基金来源',
      scale: '约 3,200 条',
      sensitivity: 'internal',
      description: '高校科研项目的结构化摘要数据，可用于科技文本理解任务。',
      createdAt: '2026-02-20'
    }
  ])

  const publishedItems = computed(() => items.value.filter(i => i.status === 'published'))
  const publishedCount = computed(() => publishedItems.value.length)
  const totalCount = computed(() => items.value.length)

  function addCatalog(data: Omit<CatalogItem, 'id' | 'createdAt'>) {
    const id = `CAT-${String(nextId++).padStart(3, '0')}`
    items.value.unshift({ ...data, id, createdAt: new Date().toISOString().slice(0, 10) })
    return id
  }

  function updateCatalog(id: string, data: Partial<CatalogItem>) {
    const item = items.value.find(i => i.id === id)
    if (item) Object.assign(item, data)
  }

  function removeCatalog(id: string) {
    items.value = items.value.filter(i => i.id !== id)
  }

  return { items, publishedItems, publishedCount, totalCount, addCatalog, updateCatalog, removeCatalog }
})
