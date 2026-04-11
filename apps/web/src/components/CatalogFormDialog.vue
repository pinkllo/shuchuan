<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useCatalogStore, type CatalogItem, type CatalogStatus, type Sensitivity } from '@/stores/catalogStore'
import { useSessionStore } from '@/stores/session'

const props = defineProps<{ visible: boolean; editItem?: CatalogItem | null }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const catalogStore = useCatalogStore()
const session = useSessionStore()

const formRef = ref()
const form = reactive({
  name: '',
  type: '文本',
  granularity: '',
  version: '',
  fields: '',
  scale: '',
  sensitivity: 'internal' as Sensitivity,
  description: '',
  status: 'draft' as CatalogStatus
})

const typeOptions = ['文本', '结构化表格', '图片', '音频', '视频', '混合']

watch(() => props.visible, (v) => {
  if (v && props.editItem) {
    Object.assign(form, {
      name: props.editItem.name,
      type: props.editItem.type,
      granularity: props.editItem.granularity,
      version: props.editItem.version,
      fields: props.editItem.fields,
      scale: props.editItem.scale,
      sensitivity: props.editItem.sensitivity,
      description: props.editItem.description,
      status: props.editItem.status
    })
  } else if (v) {
    Object.assign(form, { name: '', type: '文本', granularity: '', version: '', fields: '', scale: '', sensitivity: 'internal', description: '', status: 'draft' })
  }
})

const rules = {
  name: [{ required: true, message: '请输入目录名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  fields: [{ required: true, message: '请描述字段范围', trigger: 'blur' }]
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }

  if (props.editItem) {
    catalogStore.updateCatalog(props.editItem.id, { ...form })
    ElMessage.success('数据已更新')
  } else {
    catalogStore.addCatalog({ ...form, provider: session.name || '当前用户' })
    ElMessage.success('数据已发布')

  }
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :title="editItem ? '编辑数据' : '发布数据'"
    width="620px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="目录名称" prop="name">
        <el-input v-model="form.name" placeholder="如：课程论坛问答集" />
      </el-form-item>

      <div class="form-row">
        <el-form-item label="数据类型" prop="type" class="form-half">
          <el-select v-model="form.type" placeholder="选择类型">
            <el-option v-for="t in typeOptions" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号" class="form-half">
          <el-input v-model="form.version" placeholder="如：v2026.04" />
        </el-form-item>
      </div>

      <el-form-item label="粒度说明">
        <el-input v-model="form.granularity" placeholder="如：主题 / 帖子 / 回复" />
      </el-form-item>

      <el-form-item label="字段范围" prop="fields">
        <el-input v-model="form.fields" type="textarea" :rows="2" placeholder="描述数据包含哪些字段" />
      </el-form-item>

      <div class="form-row">
        <el-form-item label="数据规模" class="form-half">
          <el-input v-model="form.scale" placeholder="如：约 12,000 条" />
        </el-form-item>
        <el-form-item label="敏感级别" class="form-half">
          <el-radio-group v-model="form.sensitivity">
            <el-radio value="public">公开</el-radio>
            <el-radio value="internal">内部</el-radio>
            <el-radio value="sensitive">敏感</el-radio>
          </el-radio-group>
        </el-form-item>
      </div>

      <el-form-item label="发布状态">
        <el-radio-group v-model="form.status">
          <el-radio value="draft">草稿</el-radio>
          <el-radio value="published">立即发布</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="描述说明">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="补充说明数据来源、用途、脱敏情况等" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit">
        {{ editItem ? '保存修改' : '提交发布' }}
      </el-button>
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
