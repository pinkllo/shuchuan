<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useDemandStore, type DemandItem } from '@/stores/demandStore'

const props = defineProps<{ visible: boolean; demand: DemandItem | null }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const demandStore = useDemandStore()
const uploading = ref(false)
const fileList = ref<{ name: string; size: string }[]>([])

function handleFileChange(file: any) {
  const sizeMB = (file.size / 1024 / 1024).toFixed(1)
  fileList.value.push({ name: file.name, size: `${sizeMB} MB` })
  return false
}

function handleRemove(index: number) {
  fileList.value.splice(index, 1)
}

function handleUpload() {
  if (!props.demand || fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  const now = new Date().toISOString().slice(0, 10)
  const files = fileList.value.map(f => ({ ...f, uploadedAt: now }))

  setTimeout(() => {
    demandStore.addFiles(props.demand!.id, files)
    ElMessage.success(`已上传 ${files.length} 个文件`)
    uploading.value = false
    fileList.value = []
    emit('update:visible', false)
  }, 1500)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="上传数据文件"
    width="540px"
    destroy-on-close
  >
    <template v-if="demand">
      <el-alert
        :title="`向「${demand.title}」上传原始数据`"
        :description="`关联目录：${demand.catalogName} · 发起方：${demand.requester}`"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom:20px"
      />

      <el-upload
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :show-file-list="false"
        accept=".csv,.jsonl,.json,.xlsx,.txt,.zip,.tar.gz"
      >
        <el-icon class="el-icon--upload" :size="40"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 CSV / JSONL / JSON / XLSX / TXT / ZIP 格式</div>
        </template>
      </el-upload>

      <div v-if="fileList.length" class="file-list">
        <div v-for="(f, i) in fileList" :key="i" class="file-item">
          <span>📄 {{ f.name }}</span>
          <span class="file-meta">
            {{ f.size }}
            <el-button type="danger" text size="small" @click="handleRemove(i)">移除</el-button>
          </span>
        </div>
      </div>
    </template>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="fileList.length === 0" @click="handleUpload">
        {{ uploading ? '上传中...' : `上传 ${fileList.length} 个文件` }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.file-list {
  margin-top: 16px;
  display: grid;
  gap: 8px;
}
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(239, 247, 245, 0.6);
  border: 1px solid rgba(18, 68, 72, 0.08);
  font-size: 14px;
}
.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
}
</style>
