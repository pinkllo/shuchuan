<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import { fetchCatalogs } from "@/api/catalogs";
import { fetchCatalogAssets } from "@/api/catalogAssets";
import { fetchOnlineProcessors } from "@/api/processors";
import { downloadTaskResult } from "@/api/tasks";
import {
  fetchQuickTasks,
  createQuickTask,
  type QuickTaskItem,
  type QuickTaskCreatePayload,
} from "@/api/quickTasks";
import StatusBadge from "@/components/StatusBadge.vue";
import ProgressBar from "@/components/ProgressBar.vue";
import { useCapabilityStore } from "@/stores/capabilityStore";
import { useSessionStore } from "@/stores/session";
import type { CatalogItem } from "@/types/catalog";
import type { CatalogAssetItem } from "@/types/catalogAsset";
import type { Processor } from "@/types/processor";
import { taskStatusLabels, taskStatusTones, formatTaskType } from "@/types/task";

const sessionStore = useSessionStore();
const capabilityStore = useCapabilityStore();

// ── Data ──
const catalogs = ref<CatalogItem[]>([]);
const assets = ref<CatalogAssetItem[]>([]);
const onlineProcessors = ref<Processor[]>([]);
const tasks = ref<QuickTaskItem[]>([]);
const loading = ref(false);
const submitting = ref(false);
const assetsLoading = ref(false);

// ── Form ──
const selectedCatalogId = ref<number | null>(null);
const selectedAssetIds = ref<number[]>([]);
const selectedTaskType = ref("instruction");
const configModel = ref("Qwen-2.5-72B");
const configPrompt = ref("标准问答模板");
const configBatch = ref("32");

// ── Polling ──
let pollTimer: ReturnType<typeof setInterval> | null = null;

const selectedCatalog = computed(() =>
  catalogs.value.find((c) => c.id === selectedCatalogId.value) ?? null
);

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
  if (!optionMap.has(selectedTaskType.value)) {
    optionMap.set(selectedTaskType.value, selectedTaskType.value);
  }
  return Array.from(optionMap.entries()).map(([value, label]) => ({ value, label }));
});

const canSubmit = computed(() =>
  selectedCatalogId.value !== null &&
  selectedAssetIds.value.length > 0 &&
  selectedTaskType.value.trim() !== ""
);

const hasRunningTasks = computed(() =>
  tasks.value.some((t) => t.status === "queued" || t.status === "running")
);

const toneBadge: Record<string, "success" | "warning" | "danger" | "info"> = {
  queued: "warning",
  running: "info",
  completed: "success",
  failed: "danger",
};

// ── Load ──

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try {
    const [catalogList, taskList, processors] = await Promise.all([
      fetchCatalogs(token),
      fetchQuickTasks(token),
      fetchOnlineProcessors(token),
    ]);
    catalogs.value = catalogList;
    tasks.value = taskList;
    onlineProcessors.value = processors;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function refreshTasks() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    tasks.value = await fetchQuickTasks(token);
  } catch {
    /* silent refresh failure */
  }
}

watch(selectedCatalogId, async (catalogId) => {
  selectedAssetIds.value = [];
  assets.value = [];
  if (!catalogId) return;
  const token = sessionStore.accessToken;
  if (!token) return;
  assetsLoading.value = true;
  try {
    assets.value = await fetchCatalogAssets(catalogId, token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    assetsLoading.value = false;
  }
});

function selectAllAssets() {
  selectedAssetIds.value = assets.value.map((a) => a.id);
}

// ── Submit ──

async function handleSubmit() {
  const token = sessionStore.accessToken;
  if (!token || !canSubmit.value) return;
  submitting.value = true;
  try {
    const payload: QuickTaskCreatePayload = {
      catalogId: selectedCatalogId.value!,
      inputAssetIds: selectedAssetIds.value,
      taskType: selectedTaskType.value,
      config: {
        model: configModel.value,
        promptTemplate: configPrompt.value,
        batchSize: configBatch.value,
      },
    };
    const task = await createQuickTask(payload, token);
    tasks.value.unshift(task);
    ElMessage.success("任务提交成功，等待处理完成后即可下载");
    // reset form
    selectedCatalogId.value = null;
    selectedAssetIds.value = [];
    assets.value = [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    submitting.value = false;
  }
}

// ── Download ──

async function handleDownload(task: QuickTaskItem) {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await downloadTaskResult(task.id, token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

// ── Lifecycle ──

function startPolling() {
  stopPolling();
  pollTimer = setInterval(refreshTasks, 5000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

watch(hasRunningTasks, (hasRunning) => {
  if (hasRunning) {
    startPolling();
  } else {
    stopPolling();
  }
});

onMounted(async () => {
  await loadPage();
  if (hasRunningTasks.value) {
    startPolling();
  }
});

onUnmounted(() => {
  stopPolling();
});

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
</script>

<template>
  <div class="workbench" v-loading="loading">
    <!-- ── Submit Section ── -->
    <section class="submit-card">
      <h2 class="section-title">
        <span class="section-icon">🚀</span>
        提交处理任务
      </h2>
      <p class="section-desc">选择数据和处理功能，一键提交。</p>

      <div class="submit-form">
        <div class="form-row">
          <div class="form-field">
            <label class="field-label">数据目录</label>
            <el-select
              v-model="selectedCatalogId"
              filterable
              placeholder="选择目录..."
              style="width: 100%"
            >
              <el-option
                v-for="c in catalogs"
                :key="c.id"
                :label="`${c.name} (${c.version})`"
                :value="c.id"
              >
                <div class="option-row">
                  <span>{{ c.name }}</span>
                  <span class="option-meta">{{ c.version }} · {{ c.assetCount ?? 0 }}个文件</span>
                </div>
              </el-option>
            </el-select>
          </div>

          <div class="form-field">
            <label class="field-label">处理功能</label>
            <el-select
              v-model="selectedTaskType"
              filterable
              allow-create
              default-first-option
              placeholder="选择功能..."
              style="width: 100%"
            >
              <el-option
                v-for="option in taskTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </div>
        </div>

        <div v-if="selectedCatalog" class="form-field">
          <label class="field-label">
            选择输入文件
            <el-button
              v-if="assets.length > 0"
              text
              type="primary"
              size="small"
              @click="selectAllAssets"
            >
              全选
            </el-button>
          </label>
          <el-select
            v-model="selectedAssetIds"
            multiple
            filterable
            collapse-tags
            collapse-tags-tooltip
            placeholder="选择要处理的文件..."
            style="width: 100%"
            :loading="assetsLoading"
          >
            <el-option
              v-for="a in assets"
              :key="a.id"
              :label="a.fileName"
              :value="a.id"
            >
              <div class="option-row">
                <span>{{ a.fileName }}</span>
                <span class="option-meta">{{ formatFileSize(a.fileSize) }}</span>
              </div>
            </el-option>
          </el-select>
          <span v-if="selectedAssetIds.length > 0" class="field-hint">
            已选 {{ selectedAssetIds.length }} / {{ assets.length }} 个文件
          </span>
        </div>

        <div class="config-row">
          <div class="form-field form-field--narrow">
            <label class="field-label">模型</label>
            <el-select v-model="configModel" style="width: 100%">
              <el-option label="Qwen-2.5-72B" value="Qwen-2.5-72B" />
              <el-option label="Qwen-2.5-14B" value="Qwen-2.5-14B" />
              <el-option label="GLM-4-9B" value="GLM-4-9B" />
              <el-option label="DeepSeek-V3" value="DeepSeek-V3" />
            </el-select>
          </div>
          <div class="form-field form-field--narrow">
            <label class="field-label">提示词模板</label>
            <el-select v-model="configPrompt" style="width: 100%">
              <el-option label="标准问答模板" value="标准问答模板" />
              <el-option label="多轮对话模板" value="多轮对话模板" />
              <el-option label="知识抽取模板" value="知识抽取模板" />
            </el-select>
          </div>
          <div class="form-field form-field--narrow">
            <label class="field-label">批次大小</label>
            <el-input v-model="configBatch" />
          </div>
        </div>

        <div class="submit-actions">
          <el-button
            type="primary"
            :disabled="!canSubmit"
            :loading="submitting"
            @click="handleSubmit"
          >
            提交任务
          </el-button>
        </div>
      </div>
    </section>

    <!-- ── Tasks Section ── -->
    <section class="tasks-card">
      <div class="tasks-header">
        <h2 class="section-title">
          <span class="section-icon">📋</span>
          我的任务
        </h2>
        <div class="tasks-header-right">
          <span v-if="hasRunningTasks" class="poll-hint">
            <span class="poll-dot" />自动刷新中
          </span>
          <el-button text size="small" @click="refreshTasks">刷新</el-button>
        </div>
      </div>

      <el-table :data="tasks" stripe style="width: 100%" empty-text="暂无任务，请先提交一个任务">
        <el-table-column label="目录" min-width="140">
          <template #default="{ row }">
            <span class="cell-name">{{ row.catalogName }}</span>
          </template>
        </el-table-column>
        <el-table-column label="功能" width="120">
          <template #default="{ row }">
            {{ formatTaskType(row.taskType) }}
          </template>
        </el-table-column>
        <el-table-column label="文件" width="80" align="center">
          <template #default="{ row }">
            {{ row.inputAssetIds.length }}个
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <StatusBadge :label="taskStatusLabels[row.status]" :tone="toneBadge[row.status]" />
          </template>
        </el-table-column>
        <el-table-column label="进度" width="140">
          <template #default="{ row }">
            <ProgressBar v-if="row.status === 'running' || row.status === 'completed'" :value="row.progress" />
            <span v-else-if="row.status === 'failed'" class="cell-error">{{ row.note || '处理失败' }}</span>
            <span v-else class="cell-muted">等待中</span>
          </template>
        </el-table-column>
        <el-table-column label="处理器" width="110">
          <template #default="{ row }">
            <span class="cell-muted">{{ row.processorName ?? '手动' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="110">
          <template #default="{ row }">
            <span class="cell-muted">{{ formatTime(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              text
              size="small"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <span v-else-if="row.status === 'running'" class="cell-muted">处理中…</span>
            <span v-else-if="row.status === 'queued'" class="cell-muted">排队中</span>
            <span v-else class="cell-muted">—</span>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.workbench {
  display: flex;
  flex-direction: column;
  gap: var(--sp-6);
}

/* ── Submit Card ── */
.submit-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--sp-6);
}

.section-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.section-icon {
  font-size: var(--text-lg);
}

.section-desc {
  margin: var(--sp-1) 0 var(--sp-5);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.submit-form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-4);
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--sp-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.field-label {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.option-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.option-meta {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.submit-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--sp-2);
}

/* ── Tasks Card ── */
.tasks-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--sp-6);
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-4);
}

.tasks-header-right {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.poll-hint {
  display: flex;
  align-items: center;
  gap: var(--sp-1);
  font-size: var(--text-xs);
  color: var(--success);
  font-weight: var(--weight-medium);
}

.poll-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.cell-name {
  font-weight: var(--weight-medium);
  color: var(--text-primary);
}

.cell-muted {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.cell-error {
  font-size: var(--text-xs);
  color: var(--danger);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .form-row,
  .config-row {
    grid-template-columns: 1fr;
  }
}
</style>
