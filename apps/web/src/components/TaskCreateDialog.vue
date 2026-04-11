<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useTaskStore, type TaskType } from '@/stores/taskStore'
import { useDemandStore } from '@/stores/demandStore'
import { useCapabilityStore } from '@/stores/capabilityStore'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const taskStore = useTaskStore()
const demandStore = useDemandStore()
const capabilityStore = useCapabilityStore()
const formRef = ref()

const form = reactive({
  name: '',
  type: 'instruction' as TaskType,
  dataset: '',
  demandId: '',
  owner: '',
  config: {} as Record<string, any>
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择处理能力', trigger: 'change' }],
  dataset: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }]
}

const activeDemands = ref(demandStore.items.filter(d => ['approved', 'processing'].includes(d.status)))

const selectedCapability = computed(() => {
  return capabilityStore.capabilities.find(c => c.id === form.type)
})

watch(() => form.type, (newType) => {
  const cap = capabilityStore.capabilities.find(c => c.id === newType)
  form.config = {}
  if (cap?.schema) {
    cap.schema.forEach(field => {
      form.config[field.prop] = field.default || ''
    })
  }
}, { immediate: true })

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }

  const id = taskStore.addTask({
    name: form.name,
    type: form.type,
    dataset: form.dataset,
    demandId: form.demandId,
    owner: form.owner,
    config: { ...form.config }
  })

  ElMessage.success(`任务 ${id} 已创建并开始执行`)
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="注册数据处理任务"
    width="600px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="任务名称" prop="name">
        <el-input v-model="form.name" placeholder="如：教育问答指令生成" />
      </el-form-item>

      <div class="form-row">
        <el-form-item label="处理能力 (方案)" prop="type" class="form-half">
          <el-select v-model="form.type" style="width:100%">
            <el-option v-for="cap in capabilityStore.capabilities" :key="cap.id" :label="cap.name" :value="cap.id" />
          </el-select>
        </el-form-item>
      </div>

      <div class="form-row">
        <el-form-item label="数据集" prop="dataset" class="form-half">
          <el-input v-model="form.dataset" placeholder="数据集名称" />
        </el-form-item>
        <el-form-item label="关联需求" class="form-half">
          <el-select v-model="form.demandId" placeholder="可选" clearable style="width:100%">
            <el-option v-for="d in activeDemands" :key="d.id" :label="`${d.id} ${d.title}`" :value="d.id" />
          </el-select>
        </el-form-item>
      </div>

      <el-divider content-position="left">能力配置参数</el-divider>

      <template v-if="selectedCapability?.schema && selectedCapability.schema.length > 0">
        <template v-for="(field, index) in selectedCapability.schema" :key="field.prop">
          <el-form-item :label="field.label">
            <template v-if="field.type === 'select'">
              <el-select v-model="form.config[field.prop]" style="width:100%">
                <el-option v-for="opt in field.options" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </template>
            <template v-else-if="field.type === 'input'">
              <el-input v-model="form.config[field.prop]" :placeholder="field.placeholder" />
            </template>
          </el-form-item>
        </template>
      </template>

      <template v-else>
        <el-alert title="该处理能力使用系统默认配置，无需额外参数" type="info" :closable="false" show-icon />
      </template>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit">注册并执行</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-row {
  display: flex;
  gap: 16px;
}
.form-half {
  flex: 1;
}
</style>
