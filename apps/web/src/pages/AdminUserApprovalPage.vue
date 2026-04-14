<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { approveRegistration, fetchPendingRegistrations, rejectRegistration } from "@/api/admin";
import { getErrorMessage } from "@/api/http";
import MasterDetail from "@/components/MasterDetail.vue";
import ItemCard from "@/components/ItemCard.vue";
import DetailPanel from "@/components/DetailPanel.vue";
import StatusBadge from "@/components/StatusBadge.vue";
import { useSessionStore } from "@/stores/session";
import { roleLabels, type RegistrationApplication } from "@/types/auth";

const sessionStore = useSessionStore();
const applications = ref<RegistrationApplication[]>([]);
const selectedId = ref<number | null>(null);
const loading = ref(false);
const form = reactive({ role: "provider" as "provider" | "aggregator" | "consumer", reviewNote: "" });

const selected = computed(() => applications.value.find((a) => a.id === selectedId.value) ?? null);

async function loadApplications() {
  const token = sessionStore.accessToken;
  if (!token) return;
  loading.value = true;
  try { applications.value = await fetchPendingRegistrations(token); }
  catch (error) { ElMessage.error(getErrorMessage(error)); }
  finally { loading.value = false; }
}

function selectItem(id: number) {
  selectedId.value = id;
  const app = applications.value.find((a) => a.id === id);
  if (app) {
    form.role = app.requestedRole === "admin" ? "provider" : (app.requestedRole as any);
    form.reviewNote = "";
  }
}

async function handleAction(action: "approve" | "reject") {
  const token = sessionStore.accessToken;
  if (!token || !selected.value) return;
  try {
    if (action === "approve") {
      await approveRegistration(selected.value.id, form, token);
      ElMessage.success("审核通过");
    } else {
      await rejectRegistration(selected.value.id, form, token);
      ElMessage.success("已拒绝申请");
    }
    selectedId.value = null;
    await loadApplications();
  } catch (error) { ElMessage.error(getErrorMessage(error)); }
}

onMounted(loadApplications);
</script>

<template>
  <div v-loading="loading">
    <MasterDetail :has-selection="selected !== null" empty-title="选择一个申请" empty-description="从左侧列表选择注册申请以审核。">
      <template #list>
        <div class="list-header">
          <span class="list-title">注册申请 ({{ applications.length }})</span>
          <el-button text size="small" @click="loadApplications">刷新</el-button>
        </div>
        <ItemCard v-for="a in applications" :key="a.id" :selected="selectedId === a.id" @click="selectItem(a.id)">
          <div class="item-title">{{ a.displayName }}</div>
          <div class="item-meta">
            <span>@{{ a.username }}</span>
            <span>· 申请 {{ roleLabels[a.requestedRole] }}</span>
          </div>
        </ItemCard>
        <div v-if="applications.length === 0" class="list-empty">暂无待审核的申请</div>
      </template>

      <template #detail>
        <DetailPanel v-if="selected">
          <template #header>
            <h3 class="detail-title">{{ selected.displayName }}</h3>
            <StatusBadge label="待审核" tone="warning" />
          </template>

          <div class="detail-section">
            <h5 class="section-title">申请信息</h5>
            <div class="info-grid">
              <div><label>用户名</label><span>{{ selected.username }}</span></div>
              <div><label>邮箱</label><span>{{ selected.email }}</span></div>
              <div><label>申请角色</label><span>{{ roleLabels[selected.requestedRole] }}</span></div>
              <div><label>提交时间</label><span>{{ selected.createdAt }}</span></div>
            </div>
          </div>

          <div class="detail-section">
            <h5 class="section-title">申请说明</h5>
            <p class="detail-desc">{{ selected.applicationNote || '（未填写）' }}</p>
          </div>

          <div class="detail-section">
            <h5 class="section-title">审批</h5>
            <el-form label-position="top">
              <el-form-item label="批准角色">
                <el-select v-model="form.role">
                  <el-option label="数据提供者" value="provider" />
                  <el-option label="数据汇聚者" value="aggregator" />
                  <el-option label="数据使用者" value="consumer" />
                </el-select>
              </el-form-item>
              <el-form-item label="审核意见">
                <el-input v-model="form.reviewNote" type="textarea" :rows="3" />
              </el-form-item>
            </el-form>
          </div>

          <template #actions>
            <el-button type="danger" plain size="small" @click="handleAction('reject')">拒绝</el-button>
            <el-button type="primary" size="small" @click="handleAction('approve')">通过</el-button>
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
.item-title { font-weight: var(--weight-medium); font-size: var(--text-sm); color: var(--text-primary); }
.item-meta { display: flex; gap: var(--sp-1); margin-top: 2px; font-size: var(--text-xs); color: var(--text-tertiary); }
.detail-title { margin: 0 0 var(--sp-2); font-size: var(--text-lg); font-weight: var(--weight-semibold); }
.detail-section { margin-bottom: var(--sp-5); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-3); }
.info-grid div { display: flex; flex-direction: column; gap: 2px; }
.info-grid label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: var(--weight-medium); }
.info-grid span { font-size: var(--text-sm); color: var(--text-primary); }
.detail-desc { font-size: var(--text-sm); color: var(--text-secondary); line-height: var(--leading-relaxed); margin: 0; }
</style>
