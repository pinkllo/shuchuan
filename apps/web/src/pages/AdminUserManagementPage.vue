<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { disableUser, enableUser, fetchAdminUsers } from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";
import { roleLabels, type AdminUser } from "@/types/auth";

const sessionStore = useSessionStore();
const loading = ref(false);
const users = ref<AdminUser[]>([]);

async function loadUsers() {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  loading.value = true;
  try {
    users.value = await fetchAdminUsers(token);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function toggleUser(item: AdminUser) {
  const token = sessionStore.accessToken;
  if (!token) {
    return;
  }
  try {
    const next = item.status === "active"
      ? await disableUser(item.id, token)
      : await enableUser(item.id, token);
    const index = users.value.findIndex((user) => user.id === next.id);
    if (index >= 0) {
      users.value.splice(index, 1, next);
    }
    ElMessage.success(item.status === "active" ? "用户已停用" : "用户已启用");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

onMounted(loadUsers);
</script>

<template>
  <section class="surface-card">
    <div class="card-head">
      <div>
        <h3>用户管理</h3>
        <p>管理员查看平台账号，并显式切换用户启停状态。</p>
      </div>
      <el-button plain @click="loadUsers">刷新</el-button>
    </div>

    <el-table :data="users" stripe v-loading="loading">
      <el-table-column prop="id" label="用户" width="90" />
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column prop="displayName" label="显示名称" min-width="160" />
      <el-table-column prop="email" label="邮箱" min-width="220" />
      <el-table-column label="角色" width="140">
        <template #default="{ row }">
          {{ roleLabels[row.role] }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="toggleUser(row)">
            {{ row.status === "active" ? "停用" : "启用" }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
