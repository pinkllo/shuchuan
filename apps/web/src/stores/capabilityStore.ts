import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface CapSchemaField {
  prop: string
  label: string
  type: 'select' | 'input'
  options?: string[]
  placeholder?: string
  default?: string
}

export interface Capability {
  id: string
  name: string
  owner: string
  adapter: string
  status: string
  tone: 'good' | 'warn' | 'info' | 'danger'
  description: string
  configurable: boolean
  schema?: CapSchemaField[]
}

export const useCapabilityStore = defineStore('capability', () => {
  const capabilities = ref<Capability[]>([
    {
      id: 'instruction', name: '指令生成', owner: '俊才 / 当前协作', adapter: 'SDK 接入',
      status: '已接入', tone: 'good',
      description: '基于 LLM 的指令数据自动生成，支持多种提示词模板和模型选择。已集成到任务中心。',
      configurable: true,
      schema: [
        { prop: 'model', label: '模型', type: 'select', options: ['Qwen-2.5-72B', 'Qwen-2.5-14B', 'GLM-4-9B', 'DeepSeek-V3'], default: 'Qwen-2.5-72B' },
        { prop: 'batchSize', label: '批次大小', type: 'input', default: '32' },
        { prop: 'promptTemplate', label: '提示词模板', type: 'select', options: ['标准问答模板', '多轮对话模板', '知识抽取模板', '自定义模板'], default: '标准问答模板' }
      ]
    },
    {
      id: 'book_split', name: '拆书', owner: '研一同学', adapter: 'CLI / 容器',
      status: '对接中', tone: 'warn',
      description: '将长文本（教材、书籍）按章节或语义段落拆分为适合训练的片段。',
      configurable: false,
      schema: [
        { prop: 'splitStrategy', label: '拆分策略', type: 'select', options: ['按段落', '按章节', '按对话轮次', '按固定长度'], default: '按章节' },
        { prop: 'minLength', label: '最小长度（字）', type: 'input', default: '500' },
        { prop: 'maxLength', label: '最大长度（字）', type: 'input', default: '3000' }
      ]
    },
    {
      id: 'grammar_fix', name: '修改病句', owner: '张硕', adapter: 'CLI / 容器',
      status: '待接入', tone: 'danger',
      description: '自动检测和修改文本中的语法错误，生成病句-正确句对用于训练。',
      configurable: false,
      schema: [
        { prop: 'errorTypes', label: '错误类型', type: 'input', placeholder: '如：术语误用,语序错误,搭配不当', default: '术语误用,语序错误' },
        { prop: 'sampleRatio', label: '正负样本比', type: 'input', placeholder: '如：1:3', default: '1:3' }
      ]
    },
    {
      id: 'clean', name: '数据清洗', owner: '平台内置', adapter: '内置模块',
      status: '已接入', tone: 'good',
      description: '标准化字段、去空值、做敏感项检查。',
      configurable: true,
      schema: []
    },
    {
      id: 'split', name: '样本切分', owner: '平台内置', adapter: '内置模块',
      status: '已接入', tone: 'good',
      description: '按段落、对话轮次或记录粒度切分。',
      configurable: true,
      schema: [
        { prop: 'splitStrategy', label: '拆分策略', type: 'select', options: ['按段落', '按章节', '按对话轮次', '按固定长度'], default: '按段落' },
        { prop: 'minLength', label: '最小长度（字）', type: 'input', default: '200' },
        { prop: 'maxLength', label: '最大长度（字）', type: 'input', default: '2000' }
      ]
    },
    {
      id: 'quality_check', name: '质量检查', owner: '平台内置', adapter: '内置模块',
      status: '已接入', tone: 'good',
      description: '人工抽检 + 自动评分双重质检。',
      configurable: true,
      schema: []
    }
  ])

  return { capabilities }
})
