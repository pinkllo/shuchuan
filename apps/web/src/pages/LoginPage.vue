<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { login } from "@/api/auth";
import { getErrorMessage } from "@/api/http";
import { useSessionStore } from "@/stores/session";

const router = useRouter();
const route = useRoute();
const sessionStore = useSessionStore();

const form = reactive({ username: "", password: "" });
const loading = ref(false);
const sessionExpired = computed(() => route.query.reason === "session-expired");

async function handleSubmit() {
  loading.value = true;
  try {
    const payload = await login(form);
    sessionStore.setSession(payload);
    ElMessage.success("登录成功");
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/dashboard";
    await router.push(redirect);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-card">
      <header class="auth-header">
        <span class="auth-kicker">Data Flow Platform</span>
        <h1>数传协同平台</h1>
        <p>使用账号登录，进入目录发布、需求协同和交付链路。</p>
      </header>

      <el-alert v-if="sessionExpired" title="会话已失效，请重新登录。" type="warning" :closable="false" show-icon />

      <el-form :model="form" label-position="top" class="auth-form" @submit.prevent="handleSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password autocomplete="current-password" @keyup.enter="handleSubmit" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="auth-submit" @click="handleSubmit">登录系统</el-button>
      </el-form>

      <footer class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register">提交注册申请</router-link>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--sp-6);
  background: var(--bg-page);
}

.auth-card {
  width: min(440px, 100%);
  display: grid;
  gap: var(--sp-5);
  padding: var(--sp-8);
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
}

.auth-header {
  display: grid;
  gap: var(--sp-2);
}

.auth-kicker {
  font-size: var(--text-xs);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: var(--weight-semibold);
}

.auth-header h1 {
  margin: 0;
  font-size: var(--text-2xl);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
}

.auth-header p {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
}

.auth-form { display: grid; gap: var(--sp-1); }
.auth-submit { width: 100%; margin-top: var(--sp-2); }

.auth-footer {
  display: flex;
  gap: var(--sp-2);
  justify-content: center;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.auth-footer a { color: var(--accent); font-weight: var(--weight-medium); }
</style>
