<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { getErrorMessage } from "@/api/http";
import StatusPill from "@/components/StatusPill.vue";
import { usePermission } from "@/composables/usePermission";
import { useCatalogStore } from "@/stores/catalogStore";
import { useDemandStore } from "@/stores/demandStore";
import { useSessionStore } from "@/stores/session";
import { demandStatusLabels, demandStatusTones, type DemandCreatePayload, type DemandItem } from "@/types/demand";

const sessionStore = useSessionStore();
const permission = usePermission();
const catalogStore = useCatalogStore();
const demandStore = useDemandStore();

const createDialog = ref(false);
const reviewDialog = ref(false);
const assetsDialog = ref(false);
const uploadDialog = ref(false);
const currentDemand = ref<DemandItem | null>(null);
const selectedFiles = ref<File[]>([]);

const createForm = reactive<DemandCreatePayload>({
  catalogId: 0,
  title: "",
  purpose: "",
  deliveryPlan: ""
});
const reviewNote = ref("");

const catalogNameMap = computed(() => {
  return Object.fromEntries(catalogStore.items.map((item) => [item.id, item.name]));
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
    ElMessage.success("需求已提交");
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
    await demandStore.loadAssets(item.id, token);
    assetsDialog.value = true;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function handleUpload() {
  const token = sessionStore.accessToken;
  if (!token || !currentDemand.value || selectedFiles.value.length === 0) {
    return;
  }
  try {
    await demandStore.upload(currentDemand.value.id, selectedFiles.value, token);
    uploadDialog.value = false;
    selectedFiles.value = [];
    ElMessage.success("文件上传完成");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

function openReview(item: DemandItem) {
  currentDemand.value = item;
  reviewNote.value = "";
  reviewDialog.value = true;
}

function openUpload(item: DemandItem) {
  currentDemand.value = item;
  selectedFiles.value = [];
  uploadDialog.value = true;
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFiles.value = Array.from(input.files ?? []);
}

onMounted(loadPage);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>需求协同</h3>
        <p>{{ permission.isProvider ? "审批需求并上传原始数据。" : "发起需求并查看审批结果。" }}</p>
      </div>
      <div class="head-actions">
        <el-button plain @click="loadPage">刷新</el-button>
        <el-button v-if="permission.isAggregator" type="primary" @click="createDialog = true">发起需求</el-button>
      </div>
    </div>

    <el-table :data="demandStore.items" stripe v-loading="demandStore.loading">
      <el-table-column prop="id" label="需求" width="90" />
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column label="目录" min-width="180">
        <template #default="{ row }">
          {{ catalogNameMap[row.catalogId] ?? `目录 #${row.catalogId}` }}
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
          <el-button v-if="row.status === 'approved' && permission.isProvider" type="primary" link @click="openUpload(row)">上传</el-button>
          <el-button
            v-if="['data_uploaded', 'processing', 'delivered'].includes(row.status)"
            type="primary"
            link
            @click="openAssets(row)"
          >
            查看资产
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createDialog" title="发起需求" width="620px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="关联目录">
          <el-select v-model="createForm.catalogId">
            <el-option
              v-for="item in catalogStore.publishedItems"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
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

    <el-dialog v-model="uploadDialog" title="上传原始数据" width="520px">
      <input type="file" multiple @change="handleFileSelect" />
      <p class="file-note">仅走真实上传接口，不做本地成功模拟。</p>
      <ul class="file-list">
        <li v-for="file in selectedFiles" :key="file.name">{{ file.name }}</li>
      </ul>
      <template #footer>
        <el-button @click="uploadDialog = false">取消</el-button>
        <el-button type="primary" :disabled="selectedFiles.length === 0" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assetsDialog" title="已上传资产" width="640px">
      <el-table :data="currentDemand ? demandStore.assetsForDemand(currentDemand.id) : []" stripe>
        <el-table-column prop="id" label="资产" width="90" />
        <el-table-column prop="fileName" label="文件名" min-width="220" />
        <el-table-column prop="fileType" label="类型" width="150" />
        <el-table-column prop="fileSize" label="大小" width="120" />
        <el-table-column prop="uploadedAt" label="上传时间" min-width="180" />
      </el-table>
    </el-dialog>
  </section>
</template>

<style scoped>
.head-actions {
  display: flex;
  gap: 12px;
}

.file-note {
  color: var(--text-soft);
}

.file-list {
  padding-left: 18px;
}
</style>
