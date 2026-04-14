import { defineStore } from "pinia";
import { computed, ref } from "vue";

export interface CapabilitySchemaField {
  prop: string;
  label: string;
  type: "select" | "input";
  options?: string[];
  placeholder?: string;
  default?: string;
}

export interface Capability {
  id: string;
  name: string;
  owner: string;
  adapter: string;
  status: string;
  tone: "good" | "warn" | "info" | "danger";
  description: string;
  configurable: boolean;
  selectable: boolean;
  schema?: CapabilitySchemaField[];
}

export const useCapabilityStore = defineStore("capability", () => {
  const capabilities = ref<Capability[]>([
    {
      id: "instruction",
      name: "指令生成",
      owner: "一期平台主链路",
      adapter: "半接入任务登记",
      status: "半接入",
      tone: "warn",
      description: "可创建任务、记录配置、推进状态、登记产物，但不直接调用真实 LLM 执行器。",
      configurable: true,
      selectable: true,
      schema: [
        {
          prop: "model",
          label: "模型",
          type: "select",
          options: ["Qwen-2.5-72B", "Qwen-2.5-14B", "GLM-4-9B", "DeepSeek-V3"],
          default: "Qwen-2.5-72B"
        },
        {
          prop: "promptTemplate",
          label: "提示词模板",
          type: "select",
          options: ["标准问答模板", "多轮对话模板", "知识抽取模板"],
          default: "标准问答模板"
        },
        {
          prop: "batchSize",
          label: "批次大小",
          type: "input",
          default: "32"
        }
      ]
    },
    {
      id: "book_split",
      name: "拆书",
      owner: "后续外部能力",
      adapter: "待接入",
      status: "未来接入",
      tone: "info",
      description: "一期仅展示占位信息，不纳入真实主链路。",
      configurable: false,
      selectable: false
    },
    {
      id: "grammar_fix",
      name: "病句修改",
      owner: "后续外部能力",
      adapter: "待接入",
      status: "未来接入",
      tone: "info",
      description: "一期仅展示占位信息，不纳入真实主链路。",
      configurable: false,
      selectable: false
    }
  ]);

  const selectableCapabilities = computed(() => capabilities.value.filter((item) => item.selectable));

  return {
    capabilities,
    selectableCapabilities
  };
});
