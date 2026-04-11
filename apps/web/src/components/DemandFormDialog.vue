<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useCatalogStore } from '@/stores/catalogStore'
import { useDemandStore } from '@/stores/demandStore'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ visible: boolean; preselectedCatalogId?: string }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const catalogStore = useCatalogStore()
const demandStore = useDemandStore()
const session = useSessionStore()
const formRef = ref()

const form = reactive({
  title: '',
  catalogId: '',
  purpose: '',
  deliveryPlan: ''
})

const rules = {
  title: [{ required: true, message: '请输入需求标题', trigger: 'blur' }],
  catalogId: [{ required: true, message: '请选择关联目录', trigger: 'change' }],
  purpose: [{ required: true, message: '请描述用途', trigger: 'blur' }]
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }

  const catalog = catalogStore.items.find(c => c.id === form.catalogId)
  if (!catalog) return

  demandStore.addDemand({
    title: form.title,
    requester: session.name || '当前用户',
    provider: catalog.provider,
    catalogId: form.catalogId,
    catalogName: catalog.name,
    purpose: form.purpose,
    deliveryPlan: form.deliveryPlan
  })

  ElMessage.success('需求已提交，等待数据提供者审批')
  Object.assign(form, { title: '', catalogId: '', purpose: '', deliveryPlan: '' })
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="发起数据需求"
    width="580px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="需求标题" prop="title">
        <el-input v-model="form.title" placeholder="简要描述你需要什么数据，做什么用" />
      </el-form-item>

      <el-form-item label="关联数据目录" prop="catalogId">
        <el-select v-model="form.catalogId" placeholder="从已发布的目录中选择" filterable style="width:100%">
          <el-option
            v-for="item in catalogStore.publishedItems"
            :key="item.id"
            :label="`${item.name} — ${item.provider}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="用途说明" prop="purpose">
        <el-input
          v-model="form.purpose"
          type="textarea"
          :rows="3"
          placeholder="详细说明数据将用于什么场景，需要清洗到什么程度"
        />
      </el-form-item>

      <el-form-item label="期望交付节奏">
        <el-input v-model="form.deliveryPlan" placeholder="如：2026 年 5 月底前完成" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit">提交需求</el-button>
    </template>
  </el-dialog>
</template>
