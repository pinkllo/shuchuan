<script setup lang="ts">
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { roleLabels, useSessionStore, type UserRole } from "@/stores/session";

const router = useRouter();
const sessionStore = useSessionStore();

const roles: UserRole[] = ["provider", "aggregator", "consumer"];

function enterPlatform(role: UserRole) {
  sessionStore.login(role);
  ElMessage.success(`已进入前端原型：${roleLabels[role]}`);
  router.push({ name: "dashboard" });
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <header class="login-header">
        <h1>数传协同平台</h1>
        <p>请选择您的角色进入系统</p>
      </header>

      <div class="login-grid">
        <article v-for="role in roles" :key="role" class="login-role">
          <strong>{{ roleLabels[role] }}</strong>
          <el-button type="primary" @click="enterPlatform(role)">
            进入系统
          </el-button>
        </article>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f7f9fa;
  padding: 24px;
}

.login-container {
  width: 100%;
  max-width: 480px;
  background: #ffffff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-header h1 {
  margin: 0 0 12px;
  font-size: 28px;
  color: #1a1a1a;
  letter-spacing: 0.5px;
}

.login-header p {
  margin: 0;
  color: #666;
  font-size: 15px;
}

.login-grid {
  display: grid;
  gap: 16px;
}

.login-role {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-radius: 12px;
  background: #fdfdfd;
  border: 1px solid #eaeaea;
  transition: all 0.2s;
}

.login-role:hover {
  border-color: #dcdfe6;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.login-role strong {
  font-size: 16px;
  color: #333;
}
</style>
