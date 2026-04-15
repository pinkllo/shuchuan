<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import { fetchOnlineProcessors } from "@/api/processors";
import { downloadTaskResult } from "@/api/tasks";
import MasterDetail from "@/components/MasterDetail.vue";
import ItemCard from "@/components/ItemCard.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import InlineForm from "@/components/InlineForm.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import ProgressBar from "@/components/ProgressBar.vue";
import { usePermission } from "@/composables/usePermission";
import { useCapabilityStore } from "@/stores/capabilityStore";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { useTaskStore } from "@/stores/taskStore";
import type { Processor } from "@/types/processor";
import type { TaskStatus } from "@/types/task";
import { taskStatusLabels, formatTaskType } from "@/types/task";

const sessionStore = useSessionStore();
const taskStore = useTaskStore();
const demandStore = useDemandStore();
const catalogStore = useCatalogStore();
const capabilityStore = useCapabilityStore();
const permission = usePermission();

const selectedId = ref<number | null>(null);
const creating = ref(false);
const submitting = ref(false);
const statusFilter = ref<TaskStatus | "">("");
const searchQuery = ref("");

const statusDialog = ref(false);
const currentTaskId = ref<number | null>(null);
const nextStatus = ref<TaskStatus>("running");
const statusNote = ref("");

const artifactDialog = ref(false);
const artifactForm = reactive({ fileName: "", filePath: "", sampleCount: 0, note: "" });
const onlineProcessors = ref<Processor[]>([]);

const createForm = reactive({
  demandId: 0, inputAssetIds: [] as number[], taskType: "instruction",
  model: "Qwen-2.5-72B", promptTemplate: "标准问答模板", batchSize: "32"
});

const toneBadge: Record<TaskStatus, 'success' | 'warning' | 'danger' | 'info'> = {
  queued: "warning", running: "info", completed: "success", failed: "danger"
};

const filteredTasks = computed(() => {
  let list = taskStore.items;
  if (statusFilter.value) list = list.filter((t) => t.status === statusFilter.value);
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter((t) => t.taskType.toLowerCase().includes(q) || formatTaskType(t.taskType).includes(q));
  }
  return list;
});

const selected = computed(() => taskStore.items.find((t) => t.id === selectedId.value) ?? null);
const availableDemands = computed(() => demandStore.items.filter((d) => d.status === "data_uploaded" || d.status === "processing"));
const selectedDemand = computed(() => demandStore.items.find((d) => d.id === createForm.demandId) ?? null);
const availableAssets = computed(() => selectedDemand.value ? catalogStore.assetsForCatalog(selectedDemand.value.catalogId) : []);
const isManual = computed(() => selected.value && !selected.value.processorId);
const taskTypeOptions = computed(() => {
  const optionMap = new Map<string, string>();
  for (const processor of onlineProcessors.value) {
    optionMap.set(processor.taskType, `自动 · ${processor.name}`);
  }
  for (const capability of capabilityStore.selectableCapabilities) {
    if (!optionMap.has(capability.id)) {
      optionMap.set(capability.id, capability.name);
    }
  }
  if (!optionMap.has(createForm.taskType)) {
    optionMap.set(createForm.taskType, createForm.taskType);
  }
  return Array.from(optionMap.entries()).map(([value, label]) => ({ value, label }));
});

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    const [, , , processors] = await Promise.all([
      taskStore.loadAll(token),
      demandStore.loadAll(token),
      catalogStore.loadPublished(token),
      fetchOnlineProcessors(token),
    ]);
    onlineProcessors.value = processors;
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

function selectItem(id: number) { creating.value = false; selectedId.value = id; }

function startCreating() {
  selectedId.value = null; creating.value = true;
  Object.assign(createForm, { demandId: 0, inputAssetIds: [], taskType: _defaultTaskType(), model: "Qwen-2.5-72B", promptTemplate: "标准问答模板", batchSize: "32" });
}

watch(() => createForm.demandId, async (demandId) => {
  createForm.inputAssetIds = [];
  if (!demandId) return;
  const demand = demandStore.items.find((d) => d.id === demandId);
  if (!demand) return;
  const token = sessionStore.accessToken;
  if (token) try { await catalogStore.loadAssets(demand.catalogId, token); } catch {}
});

async function handleCreate() {
  const token = sessionStore.accessToken;
  if (!token) return;
  submitting.value = true;
  try {
    const task = await taskStore.submit({
      demandId: createForm.demandId, inputAssetIds: createForm.inputAssetIds, taskType: createForm.taskType,
      config: { model: createForm.model, promptTemplate: createForm.promptTemplate, batchSize: createForm.batchSize }
    }, token);
    creating.value = false; selectedId.value = task!.id;
    ElMessage.success("任务已创建");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { submitting.value = false; }
}

async function handleUpdateStatus(taskId: number, status: TaskStatus, note: string) {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await taskStore.updateStatus(taskId, status, note, token);
    ElMessage.success("任务状态已更新");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

async function handleRegisterArtifact() {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await taskStore.registerArtifact(selected.value.id, {
      artifactType: "instruction_jsonl", fileName: artifactForm.fileName,
      filePath: artifactForm.filePath, sampleCount: artifactForm.sampleCount, note: artifactForm.note
    }, token);
    artifactDialog.value = false;
    ElMessage.success("产物已登记");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

async function handleDownloadResult(taskId: number) {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await downloadTaskResult(taskId, token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function _defaultTaskType() {
  return onlineProcessors.value[0]?.taskType ?? "instruction";
}

onMounted(loadPage);
</script>

<template>
  <div>
    <MasterDetail :has-selection="selected !== null || creating" empty-title="选择一个任务" empty-description="从左侧选择任务以查看详情，或点击新建。">
      <template #list>
        <div class="list-header">
          <el-input v-model="searchQuery" placeholder="搜索任务..." size="small" clearable style="flex:1" />
          <el-select v-model="statusFilter" placeholder="状态" size="small" clearable style="width:100px">
            <el-option label="排队中" value="queued" /><el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" /><el-option label="失败" value="failed" />
          </el-select>
          <el-button type="primary" size="small" @click="startCreating">+ 新建</el-button>
        </div>
        <ItemCard v-for="t in filteredTasks" :key="t.id" :selected="selectedId === t.id" @click="selectItem(t.id)">
          <div class="item-title">{{ formatTaskType(t.taskType) }} #{{ t.id }}</div>
          <div class="item-meta">
            <StatusBadge :label="taskStatusLabels[t.status]" :tone="toneBadge[t.status]" />
            <span>{{ t.processorName ?? '手动' }}</span>
          </div>
          <ProgressBar v-if="t.status === 'running'" :value="t.progress" style="margin-top: 6px" />
        </ItemCard>
        <div v-if="filteredTasks.length === 0" class="list-empty">暂无任务</div>
      </template>

      <template #detail>
        <InlineForm v-if="creating" title="新建处理任务" :loading="submitting" @submit="handleCreate" @cancel="creating = false">
          <el-form label-position="top">
            <el-form-item label="需求">
              <el-select v-model="createForm.demandId" filterable placeholder="选择需求">
                <el-option v-for="d in availableDemands" :key="d.id" :label="`#${d.id} ${d.title}`" :value="d.id" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="availableAssets.length > 0" label="输入文件">
              <el-select v-model="createForm.inputAssetIds" multiple filterable collapse-tags placeholder="选择文件">
                <el-option v-for="a in availableAssets" :key="a.id" :label="a.fileName" :value="a.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="任务类型">
              <el-select
                v-model="createForm.taskType"
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入任务类型"
              >
                <el-option
                  v-for="option in taskTypeOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
            <div class="form-row">
              <el-form-item label="模型"><el-input v-model="createForm.model" /></el-form-item>
              <el-form-item label="批次大小"><el-input v-model="createForm.batchSize" /></el-form-item>
            </div>
            <el-form-item label="提示词模板"><el-input v-model="createForm.promptTemplate" /></el-form-item>
          </el-form>
        </InlineForm>

        <DetailPanel v-else-if="selected">
          <template #header>
            <div class="detail-head">
              <div>
                <h3 class="detail-title">{{ formatTaskType(selected.taskType) }} #{{ selected.id }}</h3>
                <StatusBadge :label="taskStatusLabels[selected.status]" :tone="toneBadge[selected.status]" />
              </div>
            </div>
          </template>

          <div class="detail-section">
            <h5 class="section-title">任务信息</h5>
            <div class="info-grid">
              <div><label>需求</label><span>#{{ selected.demandId }}</span></div>
              <div><label>处理器</label><span>{{ selected.processorName ?? '手动模式' }}</span></div>
              <div v-if="selected.config?.model"><label>模型</label><span>{{ selected.config.model }}</span></div>
              <div v-if="selected.config?.batchSize"><label>批次</label><span>{{ selected.config.batchSize }}</span></div>
            </div>
          </div>

          <div v-if="selected.status === 'running'" class="detail-section">
            <h5 class="section-title">进度</h5>
            <ProgressBar :value="selected.progress" />
            <p v-if="selected.note" class="progress-msg">{{ selected.note }}</p>
          </div>

          <div v-if="selected.note && selected.status !== 'running'" class="detail-section">
            <h5 class="section-title">备注</h5>
            <p class="detail-desc">{{ selected.note }}</p>
          </div>

          <template #actions>
            <template v-if="selected.status === 'completed'">
              <el-button type="primary" size="small" @click="handleDownloadResult(selected.id)">下载结果</el-button>
            </template>
            <template v-if="isManual">
              <el-button v-if="selected.status === 'queued'" type="primary" size="small" @click="handleUpdateStatus(selected.id, 'running', '')">开始</el-button>
              <el-button v-if="selected.status === 'running'" type="primary" size="small" @click="handleUpdateStatus(selected.id, 'completed', '')">完成</el-button>
              <el-button v-if="selected.status === 'running'" type="danger" size="small" @click="handleUpdateStatus(selected.id, 'failed', '手动标记失败')">失败</el-button>
              <el-button v-if="selected.status === 'completed'" size="small" @click="artifactDialog = true; Object.assign(artifactForm, { fileName: '', filePath: '', sampleCount: 0, note: '' })">登记产物</el-button>
            </template>
          </template>
        </DetailPanel>
      </template>
    </MasterDetail>

    <el-dialog v-model="artifactDialog" title="登记任务产物" width="520px">
      <el-form label-position="top">
        <el-form-item label="文件名"><el-input v-model="artifactForm.fileName" /></el-form-item>
        <el-form-item label="文件路径"><el-input v-model="artifactForm.filePath" placeholder="uploads/delivery/..." /></el-form-item>
        <el-form-item label="样本数"><el-input-number v-model="artifactForm.sampleCount" :min="1" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="artifactForm.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="artifactDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRegisterArtifact">登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.list-header { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); align-items: center; }
.list-empty { padding: var(--sp-6); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm); }
.item-title { font-weight: var(--weight-medium); font-size: var(--text-sm); color: var(--text-primary); }
.item-meta { display: flex; align-items: center; gap: var(--sp-2); margin-top: 4px; font-size: var(--text-xs); color: var(--text-tertiary); }
.detail-head { display: flex; justify-content: space-between; align-items: flex-start; }
.detail-head > div:first-child { display: flex; flex-direction: column; gap: var(--sp-2); }
.detail-title { margin: 0; font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.detail-section { margin-bottom: var(--sp-5); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.info-grid div { display: flex; flex-direction: column; gap: 2px; }
.info-grid label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: var(--weight-medium); }
.info-grid span { font-size: var(--text-sm); color: var(--text-primary); }
.detail-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: var(--leading-relaxed); margin: 0; }
.progress-msg { font-size: var(--text-sm); color: var(--text-secondary); margin: var(--sp-2) 0 0; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
</style>
