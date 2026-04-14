<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import SharedFilePreviewPanel from "@/components/SharedFilePreviewPanel.vue";
import StatusPill from "@/components/StatusPill.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { demandStatusLabels, demandStatusTones, type DemandCreatePayload, type DemandItem } from "@/types/demand";
import { formatCatalogAssetFileSize } from "@/utils/catalogAssetPreview";
import { buildCatalogOptionLabel, findCatalogById } from "@/utils/catalogPresentation";

const sessionStore = useSessionStore();
const permission = usePermission();
const catalogStore = useCatalogStore();
const demandStore = useDemandStore();

const createDialog = ref(false);
const reviewDialog = ref(false);
const assetsDialog = ref(false);
const currentDemand = ref<DemandItem | null>(null);
const previewAssetId = ref<number | null>(null);

const createForm = reactive<DemandCreatePayload>({
  catalogId: 0,
  title: "",
  purpose: "",
  deliveryPlan: ""
});
const reviewNote = ref("");

const selectedCatalog = computed(() => findCatalogById(catalogStore.publishedItems, createForm.catalogId));
const currentCatalog = computed(() => {
  if (!currentDemand.value) {
    return null;
  }
  return findCatalogById(catalogStore.items, currentDemand.value.catalogId);
});
const currentAssets = computed(() => {
  if (!currentDemand.value) {
    return [];
  }
  return catalogStore.assetsForCatalog(currentDemand.value.catalogId);
});
const previewAsset = computed(() => {
  if (!previewAssetId.value) {
    return null;
  }
  return currentAssets.value.find((item) => item.id === previewAssetId.value) ?? null;
});

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await Promise.all([
      demandStore.loadAll(token),
      permission.isProvider.value ? catalogStore.loadMine(token) : catalogStore.loadPublished(token)
    ]);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleCreate() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await demandStore.submit(createForm, token);
    createDialog.value = false;
    Object.assign(createForm, { catalogId: 0, title: "", purpose: "", deliveryPlan: "" });
    ElMessage.success("目录需求已提交");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleApprove() {
  const token = sessionStore.accessToken;
  if (!token || !currentDemand.value) {
    return;
  }
  try {
    await demandStore.approve(currentDemand.value.id, reviewNote.value, token);
    reviewDialog.value = false;
    reviewNote.value = "";
    ElMessage.success("需求已审批");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function openAssets(item: DemandItem) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  currentDemand.value = item;
  try {
    const assets = await catalogStore.loadAssets(item.catalogId, token);
    previewAssetId.value = assets[0]?.id ?? null;
    assetsDialog.value = true;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function openReview(item: DemandItem) {
  currentDemand.value = item;
  reviewNote.value = "";
  reviewDialog.value = true;
}

function selectPreviewAsset(assetId: number) {
  previewAssetId.value = assetId;
}

function resolveCatalog(catalogId: number) {
  return findCatalogById(catalogStore.items, catalogId);
}

onMounted(loadPage);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>需求协同</h3>
        <p>{{ permission.isProvider ? "审批按目录发起的需求。" : "按目录发起需求并查看审批结果。" }}</p>
      </div>
      <div class="head-actions">
        <el-button plain @click="loadPage">刷新</el-button>
        <el-button v-if="permission.isAggregator" type="primary" @click="createDialog = true">发起需求</el-button>
      </div>
    </div>

    <el-table :data="demandStore.items" stripe v-loading="demandStore.loading">
      <el-table-column prop="id" label="需求" width="90" />
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column label="申请目录" min-width="300">
        <template #default="{ row }">
          <div class="context-block">
            <strong>{{ resolveCatalog(row.catalogId)?.name ?? `目录 #${row.catalogId}` }}</strong>
            <small v-if="resolveCatalog(row.catalogId)">
              {{ resolveCatalog(row.catalogId)?.version }} · {{ resolveCatalog(row.catalogId)?.dataType }} ·
              {{ resolveCatalog(row.catalogId)?.granularity }} · {{ resolveCatalog(row.catalogId)?.assetCount }} 个文件
            </small>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <StatusPill :label="demandStatusLabels[row.status]" :tone="demandStatusTones[row.status]" />
        </template>
      </el-table-column>
      <el-table-column prop="approvalNote" label="审批意见" min-width="200" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending_approval' && permission.isProvider" type="primary" link @click="openReview(row)">审批</el-button>
          <el-button
            v-if="['approved', 'data_uploaded', 'processing', 'delivered'].includes(row.status)"
            type="primary"
            link
            @click="openAssets(row)"
          >
            查看目录文件
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createDialog" title="按目录发起需求" width="620px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="选择目录">
          <el-select v-model="createForm.catalogId" filterable placeholder="请选择要申请使用的目录">
            <el-option
              v-for="item in catalogStore.publishedItems"
              :key="item.id"
              :label="buildCatalogOptionLabel(item)"
              :value="item.id"
            />
          </el-select>
          <p v-if="catalogStore.publishedItems.length === 0" class="helper-text">
            当前没有可选的已发布目录，请先由数据提供者发布目录。
          </p>
          <p class="helper-text">申请的是整个目录，处理阶段再勾选目录下的具体文件。</p>
        </el-form-item>
        <div v-if="selectedCatalog" class="summary-card">
          <strong>{{ selectedCatalog.name }}</strong>
          <div class="summary-card__meta">
            <span>版本：{{ selectedCatalog.version }}</span>
            <span>类型：{{ selectedCatalog.dataType }}</span>
            <span>粒度：{{ selectedCatalog.granularity }}</span>
            <span>文件数：{{ selectedCatalog.assetCount }}</span>
            <span>敏感级别：{{ selectedCatalog.sensitivityLevel }}</span>
          </div>
          <p>{{ selectedCatalog.description }}</p>
          <small>字段：{{ selectedCatalog.fieldsDescription }}；规模：{{ selectedCatalog.scaleDescription }}</small>
        </div>
        <el-form-item label="需求标题">
          <el-input v-model="createForm.title" />
        </el-form-item>
        <el-form-item label="用途说明">
          <el-input v-model="createForm.purpose" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="交付计划">
          <el-input v-model="createForm.deliveryPlan" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewDialog" title="审批需求" width="520px">
      <el-input v-model="reviewNote" type="textarea" :rows="4" placeholder="请输入审批意见" />
      <template #footer>
        <el-button @click="reviewDialog = false">取消</el-button>
        <el-button type="primary" @click="handleApprove">通过</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assetsDialog" title="目录文件" width="980px">
      <div v-if="currentDemand && currentCatalog" class="summary-card summary-card--compact">
        <strong>{{ currentDemand.title }}</strong>
        <div class="summary-card__meta">
          <span>目录：{{ currentCatalog.name }}</span>
          <span>版本：{{ currentCatalog.version }}</span>
          <span>类型：{{ currentCatalog.dataType }}</span>
          <span>粒度：{{ currentCatalog.granularity }}</span>
        </div>
      </div>
      <div class="preview-layout">
        <el-table :data="currentAssets" stripe>
          <el-table-column prop="fileName" label="文件名" min-width="220" />
          <el-table-column prop="fileType" label="类型" width="160" />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">
              {{ formatCatalogAssetFileSize(row.fileSize) }}
            </template>
          </el-table-column>
          <el-table-column prop="uploadedAt" label="上传时间" min-width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="selectPreviewAsset(row.id)">预览</el-button>
            </template>
          </el-table-column>
        </el-table>
        <SharedFilePreviewPanel :asset="previewAsset" title="目录文件预览" />
      </div>
    </el-dialog>
  </section>
</template>

<style scoped>
.head-actions,
.summary-card__meta,
.preview-layout {
  display: flex;
  gap: 12px;
}

.helper-text,
.context-block small {
  color: var(--text-soft);
}

.helper-text {
  margin: 8px 0 0;
}

.context-block,
.summary-card {
  display: grid;
  gap: 6px;
}

.context-block strong,
.summary-card strong,
.summary-card p,
.summary-card small {
  margin: 0;
}

.summary-card {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--border-soft);
}

.summary-card__meta {
  flex-wrap: wrap;
  color: var(--text-soft);
  font-size: 13px;
}

.summary-card--compact {
  margin-bottom: 12px;
}

.preview-layout {
  align-items: flex-start;
}

.preview-layout > * {
  flex: 1;
  min-width: 0;
}
</style>
