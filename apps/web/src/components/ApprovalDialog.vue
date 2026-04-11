<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useDemandStore, type DemandItem, demandStatusLabels } from '@/stores/demandStore'

const props = defineProps<{ visible: boolean; demand: DemandItem | null }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void }>()

const demandStore = useDemandStore()
const note = ref('')

function handleApprove() {
  if (!props.demand) return
  demandStore.approveDemand(props.demand.id, note.value || '同意')
  ElMessage.success('已批准该需求')
  note.value = ''
  emit('update:visible', false)
}

function handleReject() {
  if (!props.demand) return
  if (!note.value.trim()) {
    ElMessage.warning('拒绝时请填写原因')
    return
  }
  demandStore.rejectDemand(props.demand.id, note.value)
  ElMessage.info('已拒绝该需求')
  note.value = ''
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="审批需求"
    width="560px"
    destroy-on-close
  >
    <template v-if="demand">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="需求编号">{{ demand.id }}</el-descriptions-item>
        <el-descriptions-item label="需求标题">{{ demand.title }}</el-descriptions-item>
        <el-descriptions-item label="发起方">{{ demand.requester }}</el-descriptions-item>
        <el-descriptions-item label="关联目录">{{ demand.catalogName }}</el-descriptions-item>
        <el-descriptions-item label="用途说明">{{ demand.purpose }}</el-descriptions-item>
        <el-descriptions-item label="交付节奏">{{ demand.deliveryPlan || '—' }}</el-descriptions-item>
        <el-descriptions-item label="当前状态">
          <el-tag :type="demand.status === 'pending' ? 'warning' : 'info'" size="small">
            {{ demandStatusLabels[demand.status] }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top:20px">
        <p style="margin:0 0 8px;font-weight:600">审批意见</p>
        <el-input v-model="note" type="textarea" :rows="3" placeholder="填写审批意见或拒绝原因（拒绝时必填）" />
      </div>
    </template>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="danger" plain @click="handleReject">拒绝</el-button>
      <el-button type="primary" @click="handleApprove">批准</el-button>
    </template>
  </el-dialog>
</template>
