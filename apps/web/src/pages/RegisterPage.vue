<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { submitRegistration } from "@/api/auth";
import { getErrorMessage } from "@/api/http";

const router = useRouter();

const form = reactive({
  username: "",
  displayName: "",
  password: "",
  email: "",
  requestedRole: "provider" as "provider" | "aggregator" | "consumer",
  applicationNote: ""
});
const loading = ref(false);
const createdId = ref<number | null>(null);

async function handleSubmit() {
  loading.value = true;
  try {
    const response = await submitRegistration(form);
    createdId.value = response.id;
    ElMessage.success("注册申请已提交，等待管理员审核");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-card auth-card--wide">
      <header class="auth-header">
        <p class="auth-kicker">Registration</p>
        <h1>提交注册申请</h1>
        <p>管理员审核通过后，你才能登录系统并进入对应角色链路。</p>
      </header>

      <el-alert
        v-if="createdId !== null"
        :title="`申请已提交，编号 #${createdId}`"
        description="请等待管理员审核，审核通过后再使用用户名密码登录。"
        type="success"
        :closable="false"
        show-icon
      />

      <el-form :model="form" label-position="top" class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-grid">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="3-64 位用户名" />
          </el-form-item>
          <el-form-item label="显示名称">
            <el-input v-model="form.displayName" placeholder="页面中展示的名称" />
          </el-form-item>
        </div>

        <div class="form-grid">
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="用于接收通知" />
          </el-form-item>
          <el-form-item label="申请角色">
            <el-select v-model="form.requestedRole">
              <el-option label="数据提供者" value="provider" />
              <el-option label="数据汇聚者" value="aggregator" />
              <el-option label="数据使用者" value="consumer" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 8 位" />
        </el-form-item>

        <el-form-item label="申请说明">
          <el-input
            v-model="form.applicationNote"
            type="textarea"
            :rows="4"
            placeholder="说明你要做的数据工作、预计使用场景和需要的权限。"
          />
        </el-form-item>

        <div class="auth-actions">
          <el-button @click="router.push('/login')">返回登录</el-button>
          <el-button type="primary" :loading="loading" @click="handleSubmit">提交申请</el-button>
        </div>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.auth-card {
  width: min(720px, 100%);
  display: grid;
  gap: 20px;
  padding: 32px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-soft);
}

.auth-card--wide {
  width: min(760px, 100%);
}

.auth-header {
  display: grid;
  gap: 10px;
}

.auth-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--accent-strong);
}

.auth-header h1,
.auth-header p {
  margin: 0;
}

.auth-header p {
  color: var(--text-soft);
  line-height: 1.7;
}

.auth-form {
  display: grid;
  gap: 6px;
}

.form-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.auth-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 780px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
