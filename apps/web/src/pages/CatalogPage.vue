<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import StatusPill from "@/components/StatusPill.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useSessionStore } from "@/stores/session";
import type { CatalogAssetItem } from "@/types/catalogAsset";
import {
  catalogStatusLabels,
  catalogStatusTones,
  formatSensitivity,
  type CatalogCreatePayload,
  type CatalogItem
} from "@/types/catalog";

const DEFAULT_UPLOAD_METHOD = "平台上传";
const uploadMethodOptions = [DEFAULT_UPLOAD_METHOD, "接口推送", "数据库同步", "离线拷贝"];

const sessionStore = useSessionStore();
const permission = usePermission();
const catalogStore = useCatalogStore();

const dialogVisible = ref(false);
const assetsDialogVisible = ref(false);
const publishAfterCreate = ref(false);
const search = ref("");
const currentCatalog = ref<CatalogItem | null>(null);
const createFileInput = ref<HTMLInputElement | null>(null);
const assetFileInput = ref<HTMLInputElement | null>(null);
const pendingAssetFiles = ref<File[]>([]);
const form = reactive<CatalogCreatePayload>({
  name: "",
  dataType: "text",
  granularity: "",
  version: "",
  fieldsDescription: "",
  scaleDescription: "",
  uploadMethod: DEFAULT_UPLOAD_METHOD,
  sensitivityLevel: "internal",
  description: "",
  files: []
});

const filteredCatalogs = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) {
    return catalogStore.items;
  }
  return catalogStore.items.filter((item) => item.name.toLowerCase().includes(query) || item.version.toLowerCase().includes(query));
});

const currentAssets = computed<CatalogAssetItem[]>(() => {
  if (!currentCatalog.value) {
    return [];
  }
  return catalogStore.assetsForCatalog(currentCatalog.value.id);
});

async function loadCatalogs() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    if (permission.isProvider.value) {
      await catalogStore.loadMine(token);
      return;
    }
    await catalogStore.loadPublished(token);
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
    const created = await catalogStore.submitCatalog(form, token);
    if (publishAfterCreate.value) {
      await catalogStore.publish(created.id, token);
    }
    dialogVisible.value = false;
    resetForm();
    ElMessage.success("目录已提交");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function openAssetManager(item: CatalogItem) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  currentCatalog.value = item;
  pendingAssetFiles.value = [];
  try {
    await catalogStore.loadAssets(item.id, token);
    assetsDialogVisible.value = true;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleAppendAssets() {
  const token = sessionStore.accessToken;
  if (!token || !currentCatalog.value || pendingAssetFiles.value.length === 0) {
    return;
  }
  try {
    await catalogStore.appendAssets(currentCatalog.value.id, pendingAssetFiles.value, token);
    pendingAssetFiles.value = [];
    resetAssetInput();
    ElMessage.success("目录文件已追加");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleRemoveAsset(assetId: number) {
  const token = sessionStore.accessToken;
  if (!token || !currentCatalog.value) {
    return;
  }
  try {
    await catalogStore.removeAsset(currentCatalog.value.id, assetId, token);
    ElMessage.success("目录文件已删除");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handlePublish(id: number) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await catalogStore.publish(id, token);
    ElMessage.success("目录已发布");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleArchive(id: number) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    await catalogStore.archive(id, token);
    ElMessage.success("目录已归档");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function handleCreateFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  form.files = Array.from(input.files ?? []);
}

function handleAssetFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  pendingAssetFiles.value = Array.from(input.files ?? []);
}

function resetForm() {
  Object.assign(form, {
    name: "",
    dataType: "text",
    granularity: "",
    version: "",
    fieldsDescription: "",
    scaleDescription: "",
    uploadMethod: DEFAULT_UPLOAD_METHOD,
    sensitivityLevel: "internal",
    description: "",
    files: []
  });
  publishAfterCreate.value = false;
  resetCreateInput();
}

function resetCreateInput() {
  if (createFileInput.value) {
    createFileInput.value.value = "";
  }
}

function resetAssetInput() {
  if (assetFileInput.value) {
    assetFileInput.value.value = "";
  }
}

onMounted(loadCatalogs);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>数据目录</h3>
        <p>{{ permission.isProvider ? "管理自己发布的目录与目录文件。" : "浏览已发布的数据目录。" }}</p>
      </div>
      <div class="head-actions">
        <el-input v-model="search" placeholder="按名称或版本搜索" clearable style="width: 220px" />
        <el-button plain @click="loadCatalogs">刷新</el-button>
        <el-button v-if="permission.can('catalog.create')" type="primary" @click="dialogVisible = true">新建目录</el-button>
      </div>
    </div>

    <el-table :data="filteredCatalogs" stripe v-loading="catalogStore.loading">
      <el-table-column prop="id" label="目录" width="90" />
      <el-table-column prop="name" label="名称" min-width="220" />
      <el-table-column prop="dataType" label="类型" width="120" />
      <el-table-column prop="version" label="版本" width="120" />
      <el-table-column prop="assetCount" label="文件数" width="100" />
      <el-table-column prop="uploadMethod" label="上传方式" width="140" />
      <el-table-column label="敏感级别" width="120">
        <template #default="{ row }">{{ formatSensitivity(row.sensitivityLevel) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }"><StatusPill :label="catalogStatusLabels[row.status]" :tone="catalogStatusTones[row.status]" /></template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" min-width="180" />
      <el-table-column v-if="permission.isProvider" label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openAssetManager(row)">管理文件</el-button>
          <el-button v-if="row.status === 'draft'" type="primary" link @click="handlePublish(row.id)">发布</el-button>
          <el-button v-if="row.status !== 'archived'" type="danger" link @click="handleArchive(row.id)">归档</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建数据目录" width="640px">
      <el-form :model="form" label-position="top">
        <div class="form-grid">
          <el-form-item label="目录名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="数据类型">
            <el-select v-model="form.dataType">
              <el-option label="text" value="text" />
              <el-option label="table" value="table" />
              <el-option label="image" value="image" />
            </el-select>
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="粒度说明"><el-input v-model="form.granularity" /></el-form-item>
          <el-form-item label="版本"><el-input v-model="form.version" /></el-form-item>
        </div>
        <el-form-item label="字段说明"><el-input v-model="form.fieldsDescription" type="textarea" :rows="2" /></el-form-item>
        <div class="form-grid">
          <el-form-item label="规模说明"><el-input v-model="form.scaleDescription" /></el-form-item>
          <el-form-item label="上传方式">
            <el-select v-model="form.uploadMethod" filterable allow-create default-first-option placeholder="请选择或输入上传方式">
              <el-option v-for="item in uploadMethodOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="敏感级别">
          <el-select v-model="form.sensitivityLevel">
            <el-option label="公开" value="public" />
            <el-option label="内部" value="internal" />
            <el-option label="敏感" value="sensitive" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="数据文件">
          <input ref="createFileInput" type="file" multiple @change="handleCreateFiles" />
          <p class="file-note">创建目录时至少上传一个文件，支持一次选择多个文件。</p>
          <ul class="file-list"><li v-for="file in form.files" :key="file.name">{{ file.name }}</li></ul>
        </el-form-item>
        <el-checkbox v-model="publishAfterCreate">创建后立即发布</el-checkbox>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="form.files.length === 0" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assetsDialogVisible" title="目录文件管理" width="680px">
      <div v-if="currentCatalog" class="asset-dialog">
        <p>当前目录：{{ currentCatalog.name }}，共 {{ currentCatalog.assetCount }} 个文件。</p>
        <input ref="assetFileInput" type="file" multiple @change="handleAssetFiles" />
        <ul class="file-list"><li v-for="file in pendingAssetFiles" :key="file.name">{{ file.name }}</li></ul>
        <el-button type="primary" :disabled="pendingAssetFiles.length === 0" @click="handleAppendAssets">追加上传</el-button>
        <ul class="asset-list">
          <li v-for="asset in currentAssets" :key="asset.id" class="asset-row">
            <div>
              <strong>{{ asset.fileName }}</strong>
              <p>{{ asset.fileType }} · {{ asset.fileSize }} bytes</p>
            </div>
            <el-button type="danger" link @click="handleRemoveAsset(asset.id)">删除</el-button>
          </li>
        </ul>
      </div>
    </el-dialog>
  </section>
</template>

<style scoped>
.head-actions,
.form-grid,
.asset-row {
  display: flex;
  gap: 12px;
}

.form-grid > * {
  flex: 1;
}

.file-note,
.asset-row p {
  color: var(--text-soft);
}

.file-list,
.asset-list {
  padding-left: 18px;
}

.asset-dialog {
  display: grid;
  gap: 12px;
}

.asset-row {
  align-items: center;
  justify-content: space-between;
}
</style>
