<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import StatusPill from "@/components/StatusPill.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useSessionStore } from "@/stores/session";
import {
  catalogStatusLabels,
  catalogStatusTones,
  formatSensitivity,
  type CatalogCreatePayload
} from "@/types/catalog";

const sessionStore = useSessionStore();
const permission = usePermission();
const catalogStore = useCatalogStore();

const dialogVisible = ref(false);
const publishAfterCreate = ref(false);
const search = ref("");
const form = reactive<CatalogCreatePayload>({
  name: "",
  dataType: "text",
  granularity: "",
  version: "",
  fieldsDescription: "",
  scaleDescription: "",
  sensitivityLevel: "internal",
  description: ""
});

const filteredCatalogs = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) {
    return catalogStore.items;
  }
  return catalogStore.items.filter((item) => {
    return item.name.toLowerCase().includes(query) || item.version.toLowerCase().includes(query);
  });
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

function resetForm() {
  Object.assign(form, {
    name: "",
    dataType: "text",
    granularity: "",
    version: "",
    fieldsDescription: "",
    scaleDescription: "",
    sensitivityLevel: "internal",
    description: ""
  });
  publishAfterCreate.value = false;
}

onMounted(loadCatalogs);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>数据目录</h3>
        <p>{{ permission.isProvider ? "管理自己发布的目录。" : "浏览已发布的数据目录。" }}</p>
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
      <el-table-column label="敏感级别" width="120">
        <template #default="{ row }">
          {{ formatSensitivity(row.sensitivityLevel) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <StatusPill :label="catalogStatusLabels[row.status]" :tone="catalogStatusTones[row.status]" />
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" min-width="180" />
      <el-table-column v-if="permission.isProvider" label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'draft'"
            type="primary"
            link
            @click="handlePublish(row.id)"
          >
            发布
          </el-button>
          <el-button
            v-if="row.status !== 'archived'"
            type="danger"
            link
            @click="handleArchive(row.id)"
          >
            归档
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建数据目录" width="640px">
      <el-form :model="form" label-position="top">
        <div class="form-grid">
          <el-form-item label="目录名称">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="数据类型">
            <el-select v-model="form.dataType">
              <el-option label="text" value="text" />
              <el-option label="table" value="table" />
              <el-option label="image" value="image" />
            </el-select>
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="粒度说明">
            <el-input v-model="form.granularity" />
          </el-form-item>
          <el-form-item label="版本">
            <el-input v-model="form.version" />
          </el-form-item>
        </div>
        <el-form-item label="字段说明">
          <el-input v-model="form.fieldsDescription" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="规模说明">
          <el-input v-model="form.scaleDescription" />
        </el-form-item>
        <el-form-item label="敏感级别">
          <el-select v-model="form.sensitivityLevel">
            <el-option label="公开" value="public" />
            <el-option label="内部" value="internal" />
            <el-option label="敏感" value="sensitive" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-checkbox v-model="publishAfterCreate">创建后立即发布</el-checkbox>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>
  </section>
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
