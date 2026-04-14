<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { disableUser, enableUser, fetchAdminUsers } from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import MasterDetail from "@/components/MasterDetail.vue";
import ItemCard from "@/components/ItemCard.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { useSessionStore } from "@/stores/session";
import { roleLabels, type AdminUser } from "@/types/auth";

const sessionStore = useSessionStore();
const users = ref<AdminUser[]>([]);
const selectedId = ref<number | null>(null);
const loading = ref(false);
const searchQuery = ref("");

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value;
  const q = searchQuery.value.toLowerCase();
  return users.value.filter((u) => u.username.toLowerCase().includes(q) || u.displayName.toLowerCase().includes(q));
});

const selected = computed(() => users.value.find((u) => u.id === selectedId.value) ?? null);

async function loadUsers() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try { users.value = await fetchAdminUsers(token); }
  catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { loading.value = false; }
}

async function toggleUserStatus() {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    const action = selected.value.status === "active" ? disableUser : enableUser;
    const updated = await action(selected.value.id, token);
    const index = users.value.findIndex((u) => u.id === updated.id);
    if (index !== -1) users.value.splice(index, 1, updated);
    ElMessage.success(updated.status === "active" ? "用户已启用" : "用户已停用");
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

onMounted(loadUsers);
</script>

<template>
  <div v-loading="loading">
    <MasterDetail :has-selection="selected !== null" empty-title="选择一个用户" empty-description="从左侧列表选择用户以查看详情。">
      <template #list>
        <div class="list-header">
          <el-input v-model="searchQuery" placeholder="搜索用户..." size="small" clearable style="flex:1" />
          <el-button text size="small" @click="loadUsers">刷新</el-button>
        </div>
        <ItemCard v-for="u in filteredUsers" :key="u.id" :selected="selectedId === u.id" @click="selectedId = u.id">
          <div class="item-title">{{ u.displayName }}</div>
          <div class="item-meta">
            <span>@{{ u.username }}</span>
            <StatusBadge :label="u.status === 'active' ? '活跃' : '停用'" :tone="u.status === 'active' ? 'success' : 'muted'" />
          </div>
        </ItemCard>
      </template>

      <template #detail>
        <DetailPanel v-if="selected">
          <template #header>
            <h3 class="detail-title">{{ selected.displayName }}</h3>
            <StatusBadge :label="selected.status === 'active' ? '活跃' : '停用'" :tone="selected.status === 'active' ? 'success' : 'muted'" />
          </template>

          <div class="detail-section">
            <h5 class="section-title">用户信息</h5>
            <div class="info-grid">
              <div><label>用户名</label><span>{{ selected.username }}</span></div>
              <div><label>邮箱</label><span>{{ selected.email }}</span></div>
              <div><label>角色</label><span>{{ roleLabels[selected.role] }}</span></div>
              <div><label>状态</label><span>{{ selected.status === 'active' ? '活跃' : '停用' }}</span></div>
            </div>
          </div>

          <template #actions>
            <el-button
              v-if="selected.status === 'active'" type="danger" plain size="small" @click="toggleUserStatus">停用</el-button>
            <el-button
              v-else type="primary" size="small" @click="toggleUserStatus">启用</el-button>
          </template>
        </DetailPanel>
      </template>
    </MasterDetail>
  </div>
</template>

<style scoped>
.list-header { display: flex; gap: var(--sp-2); margin-bottom: var(--sp-3); align-items: center; }
.item-title { font-weight: var(--weight-medium); font-size: var(--text-sm); color: var(--text-primary); }
.item-meta { display: flex; gap: var(--sp-2); align-items: center; margin-top: 2px; font-size: var(--text-xs); color: var(--text-tertiary); }
.detail-title { margin: 0 0 var(--sp-2); font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.detail-section { margin-bottom: var(--sp-5); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.info-grid div { display: flex; flex-direction: column; gap: 2px; }
.info-grid label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: var(--weight-medium); }
.info-grid span { font-size: var(--text-sm); color: var(--text-primary); }
</style>
