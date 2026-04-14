<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import SharedFilePreviewPanel from "@/components/SharedFilePreviewPanel.vue";
import StatusPill from "@/components/StatusPill.vue";
import { useCapabilityStore } from "@/stores/capabilityStore";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { useTaskStore } from "@/stores/taskStore";
import { taskStatusLabels, taskStatusTones, type TaskStatus } from "@/types/task";
import { formatCatalogAssetFileSize } from "@/utils/catalogAssetPreview";
import { buildCatalogAssetOptionLabel, buildDemandOptionLabel, findCatalogById } from "@/utils/catalogPresentation";

const sessionStore = useSessionStore();
const capabilityStore = useCapabilityStore();
const catalogStore = useCatalogStore();
const demandStore = useDemandStore();
const taskStore = useTaskStore();

const createDialog = ref(false);
const statusDialog = ref(false);
const artifactDialog = ref(false);
const currentTaskId = ref<number | null>(null);
const nextStatus = ref<TaskStatus>("running");
const statusNote = ref("");
const previewAssetId = ref<number | null>(null);

const createForm = reactive({
  demandId: 0,
  inputAssetIds: [] as number[],
  taskType: "instruction",
  model: "Qwen-2.5-72B",
  promptTemplate: "标准问答模板",
  batchSize: "32"
});
const artifactForm = reactive({ fileName: "", filePath: "", sampleCount: 0, note: "" });

const availableDemands = computed(() => demandStore.items.filter((item) => item.status === "data_uploaded" || item.status === "processing"));
const selectedDemand = computed(() => demandStore.items.find((item) => item.id === createForm.demandId) ?? null);
const selectedCatalog = computed(() => selectedDemand.value ? findCatalogById(catalogStore.items, selectedDemand.value.catalogId) : null);
const availableAssets = computed(() => selectedDemand.value ? catalogStore.assetsForCatalog(selectedDemand.value.catalogId) : []);
const previewAsset = computed(() => availableAssets.value.find((item) => item.id === previewAssetId.value) ?? null);

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await Promise.all([demandStore.loadAll(token), taskStore.loadAll(token), catalogStore.loadPublished(token)]);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

watch(() => createForm.demandId, async (demandId) => {
  const token = sessionStore.accessToken;
  createForm.inputAssetIds = [];
  previewAssetId.value = null;
  if (!token || !demandId) return;
  const demand = demandStore.items.find((item) => item.id === demandId);
  if (!demand) return;
  try {
    const assets = await catalogStore.loadAssets(demand.catalogId, token);
    previewAssetId.value = assets[0]?.id ?? null;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
});

async function handleCreateTask() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await taskStore.submit({
      demandId: createForm.demandId,
      inputAssetIds: createForm.inputAssetIds,
      taskType: createForm.taskType,
      config: { model: createForm.model, promptTemplate: createForm.promptTemplate, batchSize: createForm.batchSize }
    }, token);
    closeCreateDialog();
    ElMessage.success("任务已创建");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function openCreateDialog() {
  createDialog.value = true;
  createForm.demandId = 0;
  createForm.inputAssetIds = [];
  previewAssetId.value = null;
}

function closeCreateDialog() {
  createDialog.value = false;
  createForm.demandId = 0;
  createForm.inputAssetIds = [];
  previewAssetId.value = null;
}

function openStatusDialog(taskId: number, status: TaskStatus) {
  currentTaskId.value = taskId;
  nextStatus.value = status;
  statusNote.value = "";
  statusDialog.value = true;
}

async function handleUpdateStatus() {
  const token = sessionStore.accessToken;
  if (!token || currentTaskId.value === null) return;
  try {
    await taskStore.updateStatus(currentTaskId.value, nextStatus.value, statusNote.value, token);
    statusDialog.value = false;
    ElMessage.success("任务状态已更新");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function openArtifactDialog(taskId: number) {
  currentTaskId.value = taskId;
  Object.assign(artifactForm, { fileName: "", filePath: "", sampleCount: 0, note: "" });
  artifactDialog.value = true;
}

async function handleRegisterArtifact() {
  const token = sessionStore.accessToken;
  if (!token || currentTaskId.value === null) return;
  try {
    await taskStore.registerArtifact(currentTaskId.value, {
      artifactType: "instruction_jsonl",
      fileName: artifactForm.fileName,
      filePath: artifactForm.filePath,
      sampleCount: artifactForm.sampleCount,
      note: artifactForm.note
    }, token);
    artifactDialog.value = false;
    ElMessage.success("产物已登记");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

onMounted(loadPage);
</script>

<template>
  <div class="page-grid">
    <section class="surface-card">
      <div class="card-head">
        <div><h3>任务中心</h3><p>登记半接入指令生成任务，显式推进状态并登记产物。</p></div>
        <div class="head-actions"><el-button plain @click="loadPage">刷新</el-button><el-button type="primary" @click="openCreateDialog">新建任务</el-button></div>
      </div>
      <el-table :data="taskStore.items" stripe v-loading="taskStore.loading">
        <el-table-column prop="id" label="任务" width="90" />
        <el-table-column prop="demandId" label="需求" width="90" />
        <el-table-column label="输入文件" width="120"><template #default="{ row }">{{ row.inputAssetIds.length }} 个</template></el-table-column>
        <el-table-column prop="taskType" label="类型" width="120" />
        <el-table-column label="状态" width="120"><template #default="{ row }"><StatusPill :label="taskStatusLabels[row.status]" :tone="taskStatusTones[row.status]" /></template></el-table-column>
        <el-table-column prop="note" label="备注" min-width="220" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'queued'" type="primary" link @click="openStatusDialog(row.id, 'running')">开始</el-button>
            <el-button v-if="row.status === 'running'" type="primary" link @click="openStatusDialog(row.id, 'completed')">完成</el-button>
            <el-button v-if="row.status === 'running'" type="danger" link @click="openStatusDialog(row.id, 'failed')">失败</el-button>
            <el-button v-if="row.status === 'completed'" type="primary" link @click="openArtifactDialog(row.id)">登记产物</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="surface-card">
      <div class="card-head"><div><h3>能力清单</h3><p>拆书和病句修改仅作为后续能力占位，不进入一期真实主链路。</p></div></div>
      <div class="quick-actions"><article v-for="item in capabilityStore.capabilities" :key="item.id" class="quick-btn quick-btn--muted"><strong>{{ item.name }}</strong><span>{{ item.description }}</span></article></div>
    </section>

    <el-dialog v-model="createDialog" title="新建处理任务" width="760px">
      <el-form label-position="top">
        <el-form-item label="需求"><el-select v-model="createForm.demandId" filterable placeholder="请选择待处理需求"><el-option v-for="item in availableDemands" :key="item.id" :label="buildDemandOptionLabel(item, findCatalogById(catalogStore.items, item.catalogId))" :value="item.id" /></el-select></el-form-item>
        <div v-if="selectedDemand" class="summary-grid">
          <article class="summary-card"><h4>当前所选需求</h4><strong>{{ selectedDemand.title }}</strong><small>用途：{{ selectedDemand.purpose }}</small><small>交付计划：{{ selectedDemand.deliveryPlan }}</small></article>
          <article v-if="selectedCatalog" class="summary-card"><h4>目录摘要</h4><strong>{{ selectedCatalog.name }} {{ selectedCatalog.version }}</strong><small>{{ selectedCatalog.dataType }} · {{ selectedCatalog.granularity }}</small><small>{{ selectedCatalog.assetCount }} 个文件 · {{ selectedCatalog.uploadMethod }}</small></article>
        </div>
        <el-form-item label="目录文件">
          <el-select v-model="createForm.inputAssetIds" multiple filterable collapse-tags collapse-tags-tooltip placeholder="请选择要参与处理的目录文件">
            <el-option v-for="item in availableAssets" :key="item.id" :label="buildCatalogAssetOptionLabel(item)" :value="item.id" />
          </el-select>
          <p v-if="selectedCatalog" class="selection-note">当前按目录加载文件：{{ selectedCatalog.name }} {{ selectedCatalog.version }}，共 {{ availableAssets.length }} 个文件。</p>
        </el-form-item>
        <div v-if="availableAssets.length > 0" class="asset-list">
          <article v-for="item in availableAssets" :key="item.id" class="asset-row">
            <div class="asset-row__body"><strong>{{ item.fileName }}</strong><small>{{ item.fileType }} · {{ formatCatalogAssetFileSize(item.fileSize) }} · {{ item.uploadedAt }}</small></div>
            <div class="asset-row__actions"><small v-if="createForm.inputAssetIds.includes(item.id)">已勾选</small><el-button type="primary" link @click="previewAssetId = item.id">预览</el-button></div>
          </article>
        </div>
        <SharedFilePreviewPanel :asset="previewAsset" title="任务输入文件预览" />
        <el-form-item label="能力"><el-select v-model="createForm.taskType"><el-option v-for="item in capabilityStore.selectableCapabilities" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
        <div class="form-grid"><el-form-item label="模型"><el-input v-model="createForm.model" /></el-form-item><el-form-item label="批次大小"><el-input v-model="createForm.batchSize" /></el-form-item></div>
        <el-form-item label="提示词模板"><el-input v-model="createForm.promptTemplate" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="closeCreateDialog">取消</el-button><el-button type="primary" :disabled="createForm.inputAssetIds.length === 0" @click="handleCreateTask">创建</el-button></template>
    </el-dialog>

    <el-dialog v-model="statusDialog" title="更新任务状态" width="520px">
      <el-form label-position="top"><el-form-item label="目标状态"><el-input :model-value="taskStatusLabels[nextStatus]" disabled /></el-form-item><el-form-item label="备注"><el-input v-model="statusNote" type="textarea" :rows="4" /></el-form-item></el-form>
      <template #footer><el-button @click="statusDialog = false">取消</el-button><el-button type="primary" @click="handleUpdateStatus">提交</el-button></template>
    </el-dialog>

    <el-dialog v-model="artifactDialog" title="登记任务产物" width="560px">
      <el-form label-position="top">
        <el-form-item label="文件名"><el-input v-model="artifactForm.fileName" /></el-form-item>
        <el-form-item label="文件路径"><el-input v-model="artifactForm.filePath" placeholder="例如 uploads/delivery/3/result.jsonl" /></el-form-item>
        <el-form-item label="样本数"><el-input-number v-model="artifactForm.sampleCount" :min="1" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="artifactForm.note" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="artifactDialog = false">取消</el-button><el-button type="primary" @click="handleRegisterArtifact">登记</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-actions,.form-grid,.summary-grid,.asset-row,.asset-row__actions{display:flex;gap:12px}
.form-grid>*,.summary-grid>*{flex:1}
.selection-note,.summary-card small,.asset-row__body small,.asset-row__actions small{color:var(--text-soft)}
.selection-note{margin:8px 0 0}
.summary-grid,.asset-list{margin-bottom:16px}
.summary-card,.asset-row{padding:14px 16px;border-radius:18px;border:1px solid var(--border-soft);background:var(--surface-strong)}
.summary-card,.asset-row__body,.asset-list{display:grid;gap:6px}
.summary-card h4,.summary-card strong,.summary-card small,.asset-row__body strong,.asset-row__body small{margin:0}
.asset-row{align-items:center;justify-content:space-between}
.asset-row__actions{align-items:center}
</style>
