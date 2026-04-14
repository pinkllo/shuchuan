<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

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
import { useSessionStore } from "@/stores/session";
import type { CatalogItem, CatalogStatus } from "@/types/catalog";
import { catalogStatusLabels } from "@/types/catalog";

const sessionStore = useSessionStore();
const catalogStore = useCatalogStore();
const permission = usePermission();

const selectedId = ref<number | null>(null);
const creating = ref(false);
const searchQuery = ref("");
const statusFilter = ref<CatalogStatus | "">("");
const submitting = ref(false);
const previewAsset = ref<any>(null);

const createForm = reactive({
  name: "", dataType: "text", granularity: "document", version: "1.0",
  fieldsDescription: "", scaleDescription: "", uploadMethod: "batch",
  sensitivityLevel: "internal", description: "", files: [] as File[]
});

const toneBadge: Record<string, 'success' | 'warning' | 'info' | 'muted'> = {
  draft: "warning", published: "success", archived: "muted"
};

const filteredCatalogs = computed(() => {
  let list = catalogStore.items;
  if (statusFilter.value) list = list.filter((c) => c.status === statusFilter.value);
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter((c) => c.name.toLowerCase().includes(q));
  }
  return list;
});

const selected = computed(() => catalogStore.items.find((c) => c.id === selectedId.value) ?? null);
const assets = computed(() => selected.value ? catalogStore.assetsForCatalog(selected.value.id) : []);
const fileItems = computed<FileItem[]>(() => assets.value.map((a) => ({
  id: a.id, fileName: a.fileName, fileSize: a.fileSize, fileType: a.fileType, uploadedAt: a.uploadedAt
})));

async function loadPage() {
  const token = sessionStore.accessToken;
  if (!token) return;
  try {
    if (permission.isProvider.value) await catalogStore.loadMine(token);
    else await catalogStore.loadPublished(token);
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

function selectItem(id: number) {
  creating.value = false;
  selectedId.value = id;
  loadAssets(id);
}

async function loadAssets(catalogId: number) {
  const token = sessionStore.accessToken;
  if (!token) return;
  try { await catalogStore.loadAssets(catalogId, token); } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

function startCreating() {
  selectedId.value = null;
  creating.value = true;
  Object.assign(createForm, {
    name: "", dataType: "text", granularity: "document", version: "1.0",
    fieldsDescription: "", scaleDescription: "", uploadMethod: "batch",
    sensitivityLevel: "internal", description: "", files: []
  });
}

function cancelCreating() { creating.value = false; }

async function handleCreate() {
  const token = sessionStore.accessToken;
  if (!token) return;
  submitting.value = true;
  try {
    const catalog = await catalogStore.submitCatalog({ ...createForm }, token);
    creating.value = false;
    selectedId.value = catalog.id;
    ElMessage.success("目录已创建");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { submitting.value = false; }
}

async function handlePublish() {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await catalogStore.publish(selected.value.id, token);
    ElMessage.success("目录已发布");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

async function handleArchive() {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await catalogStore.archive(selected.value.id, token);
    ElMessage.success("目录已归档");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

async function handleUploadFiles(files: FileList) {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await catalogStore.appendAssets(selected.value.id, Array.from(files), token);
    ElMessage.success(`${files.length} 个文件已上传`);
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

async function handleDeleteFile(file: FileItem) {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    await catalogStore.removeAsset(selected.value.id, file.id, token);
    ElMessage.success("文件已删除");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

onMounted(loadPage);
</script>

<template>
  <div>
    <MasterDetail :has-selection="selected !== null || creating" empty-title="选择一个目录" empty-description="从左侧选择目录以查看详情，或点击新建。">
      <template #list>
        <div class="list-header">
          <el-input v-model="searchQuery" placeholder="搜索目录..." size="small" clearable />
          <el-select v-model="statusFilter" placeholder="状态" size="small" clearable style="width: 110px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
          <el-button v-if="permission.isProvider.value" type="primary" size="small" @click="startCreating">+ 新建</el-button>
        </div>
        <ItemCard v-for="c in filteredCatalogs" :key="c.id" :selected="selectedId === c.id" @click="selectItem(c.id)">
          <div class="item-title">{{ c.name }} <span class="item-version">{{ c.version }}</span></div>
          <div class="item-meta">
            <StatusBadge :label="catalogStatusLabels[c.status]" :tone="toneBadge[c.status]" />
            <span>{{ c.assetCount ?? 0 }} 个文件</span>
          </div>
        </ItemCard>
        <div v-if="filteredCatalogs.length === 0" class="list-empty">暂无目录</div>
      </template>

      <template #detail>
        <!-- Creating Mode -->
        <InlineForm v-if="creating" title="新建数据目录" :loading="submitting" @submit="handleCreate" @cancel="cancelCreating">
          <el-form label-position="top">
            <el-form-item label="目录名称"><el-input v-model="createForm.name" /></el-form-item>
            <div class="form-row">
              <el-form-item label="数据类型"><el-input v-model="createForm.dataType" /></el-form-item>
              <el-form-item label="版本"><el-input v-model="createForm.version" /></el-form-item>
            </div>
            <div class="form-row">
              <el-form-item label="粒度"><el-input v-model="createForm.granularity" /></el-form-item>
              <el-form-item label="敏感级别">
                <el-select v-model="createForm.sensitivityLevel"><el-option label="公开" value="public" /><el-option label="内部" value="internal" /><el-option label="敏感" value="sensitive" /></el-select>
              </el-form-item>
            </div>
            <el-form-item label="字段说明"><el-input v-model="createForm.fieldsDescription" type="textarea" :rows="2" /></el-form-item>
            <el-form-item label="规模描述"><el-input v-model="createForm.scaleDescription" /></el-form-item>
            <el-form-item label="描述"><el-input v-model="createForm.description" type="textarea" :rows="2" /></el-form-item>
          </el-form>
        </InlineForm>

        <!-- Viewing Mode -->
        <DetailPanel v-else-if="selected">
          <template #header>
            <div class="detail-head">
              <div>
                <h3 class="detail-title">{{ selected.name }} <span class="item-version">{{ selected.version }}</span></h3>
                <StatusBadge :label="catalogStatusLabels[selected.status]" :tone="toneBadge[selected.status]" />
              </div>
              <div v-if="permission.isProvider.value" class="detail-actions">
                <el-button v-if="selected.status === 'draft'" type="primary" size="small" @click="handlePublish">发布</el-button>
                <el-button v-if="selected.status === 'published'" size="small" @click="handleArchive">归档</el-button>
              </div>
            </div>
          </template>

          <div class="detail-section">
            <h5 class="section-title">基本信息</h5>
            <div class="info-grid">
              <div><label>数据类型</label><span>{{ selected.dataType }}</span></div>
              <div><label>粒度</label><span>{{ selected.granularity }}</span></div>
              <div><label>敏感级别</label><span>{{ selected.sensitivityLevel }}</span></div>
              <div><label>上传方式</label><span>{{ selected.uploadMethod }}</span></div>
            </div>
            <p v-if="selected.description" class="detail-desc">{{ selected.description }}</p>
          </div>

          <div class="detail-section">
            <h5 class="section-title">文件列表（{{ fileItems.length }}）</h5>
            <FileList
              :files="fileItems"
              :editable="permission.isProvider.value && selected.status === 'draft'"
              @upload="handleUploadFiles"
              @delete="handleDeleteFile"
              @preview="(f) => previewAsset = assets.find((a) => a.id === f.id) ?? null"
            />
          </div>

          <SharedFilePreviewPanel v-if="previewAsset" :asset="previewAsset" title="文件预览" />
        </DetailPanel>
      </template>
    </MasterDetail>
  </div>
</template>

<style scoped>
.list-header { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); align-items: center; }
.list-empty { padding: var(--sp-6); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm); }
.item-title { font-weight: var(--weight-medium); font-size: var(--text-sm); color: var(--text-primary); }
.item-version { color: var(--text-tertiary); font-weight: var(--weight-normal); }
.item-meta { display: flex; align-items: center; gap: var(--sp-2); margin-top: 4px; font-size: var(--text-xs); color: var(--text-tertiary); }
.detail-head { display: flex; justify-content: space-between; align-items: flex-start; }
.detail-head > div:first-child { display: flex; flex-direction: column; gap: var(--sp-2); }
.detail-title { margin: 0; font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.detail-actions { display: flex; gap: var(--sp-2); }
.detail-section { margin-bottom: var(--sp-5); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.info-grid div { display: flex; flex-direction: column; gap: 2px; }
.info-grid label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: var(--weight-medium); }
.info-grid span { font-size: var(--text-sm); color: var(--text-primary); }
.detail-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: var(--leading-relaxed); margin: var(--sp-3) 0 0; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
</style>
