<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { getErrorMessage } from "@/api/http";
import StatusPill from "@/components/StatusPill.vue";
import { useCapabilityStore } from "@/stores/capabilityStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { useTaskStore } from "@/stores/taskStore";
import { taskStatusLabels, taskStatusTones, type TaskStatus } from "@/types/task";
const sessionStore = useSessionStore();
const capabilityStore = useCapabilityStore();
const demandStore = useDemandStore();
const taskStore = useTaskStore();
const createDialog = ref(false);
const statusDialog = ref(false);
const artifactDialog = ref(false);
const currentTaskId = ref<number | null>(null);
const nextStatus = ref<TaskStatus>("running");
const statusNote = ref("");
const createForm = reactive({
  demandId: 0,
  inputAssetId: 0,
  taskType: "instruction",
  model: "Qwen-2.5-72B",
  promptTemplate: "标准问答模板",
  batchSize: "32"
});
const artifactForm = reactive({
  fileName: "",
  filePath: "",
  sampleCount: 0,
  note: ""
});
const availableDemands = computed(() => {
  return demandStore.items.filter((item) => item.status === "data_uploaded" || item.status === "processing");
});
const availableAssets = computed(() => {
  if (!createForm.demandId) {
    return [];
  }
  return demandStore.assetsForDemand(createForm.demandId);
});

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await Promise.all([demandStore.loadAll(token), taskStore.loadAll(token)]);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

watch(
  () => createForm.demandId,
  async (demandId) => {
    const token = sessionStore.accessToken;
    if (!token || !demandId) {
      return;
    }
    try {
      await demandStore.loadAssets(demandId, token);
    } catch (error) {
      ElMessage.error(getErrorMessage(error));
    }
  }
);

async function handleCreateTask() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await taskStore.submit(
      {
        demandId: createForm.demandId,
        inputAssetId: createForm.inputAssetId,
        taskType: createForm.taskType,
        config: {
          model: createForm.model,
          promptTemplate: createForm.promptTemplate,
          batchSize: createForm.batchSize
        }
      },
      token
    );
    createDialog.value = false;
    ElMessage.success("任务已创建");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function openStatusDialog(taskId: number, status: TaskStatus) {
  currentTaskId.value = taskId;
  nextStatus.value = status;
  statusNote.value = "";
  statusDialog.value = true;
}

async function handleUpdateStatus() {
  const token = sessionStore.accessToken;
  if (!token || currentTaskId.value === null) {
    return;
  }
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
  if (!token || currentTaskId.value === null) {
    return;
  }
  try {
    await taskStore.registerArtifact(
      currentTaskId.value,
      {
        artifactType: "instruction_jsonl",
        fileName: artifactForm.fileName,
        filePath: artifactForm.filePath,
        sampleCount: artifactForm.sampleCount,
        note: artifactForm.note
      },
      token
    );
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
        <div>
          <h3>任务中心</h3>
          <p>登记半接入指令生成任务，显式推进状态并登记产物。</p>
        </div>
        <div class="head-actions">
          <el-button plain @click="loadPage">刷新</el-button>
          <el-button type="primary" @click="createDialog = true">新建任务</el-button>
        </div>
      </div>

      <el-table :data="taskStore.items" stripe v-loading="taskStore.loading">
        <el-table-column prop="id" label="任务" width="90" />
        <el-table-column prop="demandId" label="需求" width="90" />
        <el-table-column prop="taskType" label="类型" width="120" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusPill :label="taskStatusLabels[row.status]" :tone="taskStatusTones[row.status]" />
          </template>
        </el-table-column>
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
      <div class="card-head">
        <div>
          <h3>能力清单</h3>
          <p>拆书和病句修改仅作为后续能力占位，不进入一期真实主链路。</p>
        </div>
      </div>
      <div class="quick-actions">
        <article v-for="item in capabilityStore.capabilities" :key="item.id" class="quick-btn quick-btn--muted">
          <strong>{{ item.name }}</strong>
          <span>{{ item.description }}</span>
        </article>
      </div>
    </section>

    <el-dialog v-model="createDialog" title="新建处理任务" width="620px">
      <el-form label-position="top">
        <el-form-item label="需求">
          <el-select v-model="createForm.demandId">
            <el-option
              v-for="item in availableDemands"
              :key="item.id"
              :label="`${item.id} - ${item.title}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="输入资产">
          <el-select v-model="createForm.inputAssetId">
            <el-option
              v-for="item in availableAssets"
              :key="item.id"
              :label="`${item.id} - ${item.fileName}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="能力">
          <el-select v-model="createForm.taskType">
            <el-option
              v-for="item in capabilityStore.selectableCapabilities"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="模型">
            <el-input v-model="createForm.model" />
          </el-form-item>
          <el-form-item label="批次大小">
            <el-input v-model="createForm.batchSize" />
          </el-form-item>
        </div>
        <el-form-item label="提示词模板">
          <el-input v-model="createForm.promptTemplate" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="statusDialog" title="更新任务状态" width="520px">
      <el-form label-position="top">
        <el-form-item label="目标状态">
          <el-input :model-value="taskStatusLabels[nextStatus]" disabled />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="statusNote" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateStatus">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="artifactDialog" title="登记任务产物" width="560px">
      <el-form label-position="top">
        <el-form-item label="文件名">
          <el-input v-model="artifactForm.fileName" />
        </el-form-item>
        <el-form-item label="文件路径">
          <el-input v-model="artifactForm.filePath" placeholder="例如 uploads/delivery/3/result.jsonl" />
        </el-form-item>
        <el-form-item label="样本数">
          <el-input-number v-model="artifactForm.sampleCount" :min="1" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="artifactForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="artifactDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRegisterArtifact">登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-actions,
.form-grid {
  display: flex;
  gap: 12px;
}

.form-grid > * {
  flex: 1;
}
</style>
