<script setup lang="ts">
import { reactive, ref, onMounted } from "vue";
import { ElMessage } from "element-plus";

import {
  approveRegistration,
  fetchPendingRegistrations,
  rejectRegistration
} from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";
import { roleLabels, type RegistrationApplication } from "@/types/auth";

const sessionStore = useSessionStore();
const loading = ref(false);
const dialogVisible = ref(false);
const currentApplication = ref<RegistrationApplication | null>(null);
const applications = ref<RegistrationApplication[]>([]);
const form = reactive({
  role: "provider" as "provider" | "aggregator" | "consumer",
  reviewNote: ""
});

async function loadApplications() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  loading.value = true;
  try {
    applications.value = await fetchPendingRegistrations(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function openDialog(item: RegistrationApplication) {
  currentApplication.value = item;
  form.role = item.requestedRole === "admin" ? "provider" : item.requestedRole;
  form.reviewNote = "";
  dialogVisible.value = true;
}

async function handleAction(action: "approve" | "reject") {
  const token = sessionStore.accessToken;
  if (!token || !currentApplication.value) {
    return;
  }
  try {
    if (action === "approve") {
      await approveRegistration(currentApplication.value.id, form, token);
      ElMessage.success("审核通过");
    } else {
      await rejectRegistration(currentApplication.value.id, form, token);
      ElMessage.success("已拒绝申请");
    }
    dialogVisible.value = false;
    await loadApplications();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

onMounted(loadApplications);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>注册审核</h3>
        <p>管理员审批注册申请并显式分配业务角色。</p>
      </div>
      <el-button plain @click="loadApplications">刷新</el-button>
    </div>

    <el-table :data="applications" stripe v-loading="loading">
      <el-table-column prop="id" label="申请" width="90" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="displayName" label="显示名称" min-width="160" />
      <el-table-column prop="email" label="邮箱" min-width="220" />
      <el-table-column label="申请角色" width="140">
        <template #default="{ row }">
          {{ roleLabels[row.requestedRole] }}
        </template>
      </el-table-column>
      <el-table-column prop="applicationNote" label="申请说明" min-width="260" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDialog(row)">审核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="审核注册申请" width="520px">
      <template v-if="currentApplication">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="用户名">{{ currentApplication.username }}</el-descriptions-item>
          <el-descriptions-item label="申请说明">{{ currentApplication.applicationNote }}</el-descriptions-item>
        </el-descriptions>
        <el-form label-position="top" class="review-form">
          <el-form-item label="批准角色">
            <el-select v-model="form.role">
              <el-option label="数据提供者" value="provider" />
              <el-option label="数据汇聚者" value="aggregator" />
              <el-option label="数据使用者" value="consumer" />
            </el-select>
          </el-form-item>
          <el-form-item label="审核意见">
            <el-input v-model="form.reviewNote" type="textarea" :rows="4" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="danger" plain @click="handleAction('reject')">拒绝</el-button>
        <el-button type="primary" @click="handleAction('approve')">通过</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.review-form {
  margin-top: 16px;
}
</style>
