<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import MasterDetail from "@/components/MasterDetail.vue";
import ItemCard from "@/components/ItemCard.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import InlineForm from "@/components/InlineForm.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import FileList from "@/components/FileList.vue";
import type { FileItem } from "@/components/FileList.vue";
import SharedFilePreviewPanel from "@/components/SharedFilePreviewPanel.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import type { DemandItem, DemandStatus } from "@/types/demand";
import { demandStatusLabels } from "@/types/demand";

const sessionStore = useSessionStore();
const demandStore = useDemandStore();
const catalogStore = useCatalogStore();
const permission = usePermission();

const selectedId = ref<number | null>(null);
const creating = ref(false);
const submitting = ref(false);
const approveNote = ref("");
const previewAsset = ref<any>(null);
const assetsLoading = ref(false);

const createForm = reactive({ catalogId: 0, title: "", purpose: "", deliveryPlan: "" });

const toneBadge: Record<DemandStatus, 'success' | 'warning' | 'danger' | 'info' | 'muted'> = {
  pending_approval: "warning", approved: "info", rejected: "danger",
  data_uploaded: "info", processing: "info", delivered: "success"
};

const statusGroups: { key: DemandStatus[]; label: string }[] = [
  { key: ["pending_approval"], label: "待审批" },
  { key: ["approved", "data_uploaded"], label: "已获批" },
  { key: ["processing"], label: "处理中" },
  { key: ["delivered"], label: "已交付" },
  { key: ["rejected"], label: "已驳回" },
];

const groupedDemands = computed(() =>
  statusGroups.map((g) => ({
    label: g.label,
    items: demandStore.items.filter((d) => g.key.includes(d.status)),
  })).filter((g) => g.items.length > 0)
);

const selected = computed(() => demandStore.items.find((d) => d.id === selectedId.value) ?? null);
const selectedCatalog = computed(() => selected.value ? catalogStore.items.find((c) => c.id === selected.value!.catalogId) ?? null : null);

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    await Promise.all([
      demandStore.loadAll(token),
      permission.isAggregator.value ? catalogStore.loadPublished(token) : catalogStore.loadMine(token)
    ]);
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

function selectItem(id: number) {
  creating.value = false;
  selectedId.value = id;
  previewAsset.value = null;
  loadDemandAssets(id);
}

async function loadDemandAssets(demandId: number) {
  const demand = demandStore.items.find((d) => d.id === demandId);
  if (!demand) return;
  const token = sessionStore.accessToken;
  if (!token) return;
  assetsLoading.value = true;
  try {
    await catalogStore.loadAssets(demand.catalogId, token);
  } catch { /* aggregator may not have access to some catalogs */ }
  finally { assetsLoading.value = false; }
}

const catalogAssets = computed(() => {
  if (!selected.value || !selectedCatalog.value) return [];
  return catalogStore.assetsForCatalog(selectedCatalog.value.id);
});

const catalogFileItems = computed<FileItem[]>(() => catalogAssets.value.map((a) => ({
  id: a.id, fileName: a.fileName, fileSize: a.fileSize, fileType: a.fileType, uploadedAt: a.uploadedAt
})));

function startCreating() {
  selectedId.value = null; creating.value = true;
  Object.assign(createForm, { catalogId: 0, title: "", purpose: "", deliveryPlan: "" });
}

async function handleCreate() {
  const token = sessionStore.accessToken;
  if (!token) return;
  submitting.value = true;
  try {
    const demand = await demandStore.submit(createForm, token);
    creating.value = false; selectedId.value = demand.id;
    ElMessage.success("需求已创建");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { submitting.value = false; }
}

async function handleApprove() {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await demandStore.approve(selected.value.id, approveNote.value, token);
    approveNote.value = "";
    ElMessage.success("需求已审批");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}


onMounted(loadPage);
</script>

<template>
  <div>
    <MasterDetail :has-selection="selected !== null || creating" empty-title="选择一个需求" empty-description="从左侧选择需求以查看详情。">
      <template #list>
        <div class="list-header">
          <span class="list-title">需求列表</span>
          <el-button v-if="permission.isAggregator.value" type="primary" size="small" @click="startCreating">+ 新建</el-button>
        </div>
        <template v-for="group in groupedDemands" :key="group.label">
          <div class="group-label">{{ group.label }} ({{ group.items.length }})</div>
          <ItemCard v-for="d in group.items" :key="d.id" :selected="selectedId === d.id" @click="selectItem(d.id)">
            <div class="item-title">{{ d.title }}</div>
            <div class="item-meta">
              <StatusBadge :label="demandStatusLabels[d.status]" :tone="toneBadge[d.status]" />
              <span>需求 #{{ d.id }}</span>
            </div>
          </ItemCard>
        </template>
        <div v-if="groupedDemands.length === 0" class="list-empty">暂无需求</div>
      </template>

      <template #detail>
        <InlineForm v-if="creating" title="新建需求" :loading="submitting" @submit="handleCreate" @cancel="creating = false">
          <el-form label-position="top">
            <el-form-item label="目录">
              <el-select v-model="createForm.catalogId" filterable placeholder="选择数据目录">
                <el-option v-for="c in catalogStore.publishedItems" :key="c.id" :label="`${c.name} ${c.version}`" :value="c.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="需求标题"><el-input v-model="createForm.title" /></el-form-item>
            <el-form-item label="用途"><el-input v-model="createForm.purpose" type="textarea" :rows="2" /></el-form-item>
            <el-form-item label="交付计划"><el-input v-model="createForm.deliveryPlan" /></el-form-item>
          </el-form>
        </InlineForm>

        <DetailPanel v-else-if="selected">
          <template #header>
            <div class="detail-head">
              <div>
                <h3 class="detail-title">{{ selected.title }}</h3>
                <StatusBadge :label="demandStatusLabels[selected.status]" :tone="toneBadge[selected.status]" />
              </div>
            </div>
          </template>

          <div class="detail-section">
            <h5 class="section-title">需求信息</h5>
            <div class="info-grid">
              <div><label>用途</label><span>{{ selected.purpose }}</span></div>
              <div><label>交付计划</label><span>{{ selected.deliveryPlan }}</span></div>
            </div>
          </div>

          <div v-if="selectedCatalog" class="detail-section">
            <h5 class="section-title">关联目录</h5>
            <div class="info-grid">
              <div><label>名称</label><span>{{ selectedCatalog.name }} {{ selectedCatalog.version }}</span></div>
              <div><label>数据类型</label><span>{{ selectedCatalog.dataType }}</span></div>
              <div><label>文件数</label><span>{{ selectedCatalog.assetCount }} 个</span></div>
              <div><label>状态</label><span>{{ selectedCatalog.status }}</span></div>
            </div>
          </div>

          <div v-if="catalogFileItems.length > 0" class="detail-section">
            <h5 class="section-title">目录文件（{{ catalogFileItems.length }}）</h5>
            <FileList
              :files="catalogFileItems"
              :editable="false"
              :loading="assetsLoading"
              @preview="(f) => previewAsset = catalogAssets.find((a) => a.id === f.id) ?? null"
            />
          </div>

          <SharedFilePreviewPanel v-if="previewAsset" :asset="previewAsset" title="文件预览" />

          <div v-if="selected.approvalNote" class="detail-section">
            <h5 class="section-title">审批备注</h5>
            <p class="detail-desc">{{ selected.approvalNote }}</p>
          </div>

          <template #actions>
            <template v-if="permission.isProvider.value && selected.status === 'pending_approval'">
              <el-input v-model="approveNote" placeholder="审批备注（可选）" size="small" style="flex:1" />
              <el-button type="primary" size="small" @click="handleApprove">审批通过</el-button>
            </template>
          </template>
        </DetailPanel>
      </template>
    </MasterDetail>
  </div>
</template>

<style scoped>
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--sp-3); }
.list-title { font-size: var(--text-sm); font-weight: var(--weight-semibold); color: var(--text-secondary); }
.list-empty { padding: var(--sp-6); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm); }
.group-label { font-size: var(--text-xs); font-weight: var(--weight-semibold); color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; padding: var(--sp-2) var(--sp-1); margin-top: var(--sp-2); }
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
</style>
