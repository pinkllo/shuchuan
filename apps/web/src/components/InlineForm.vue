<script setup lang="ts">
defineProps<{
  title: string;
  loading?: boolean;
}>();

defineEmits<{
  submit: [];
  cancel: [];
}>();
</script>

<template>
  <div class="inline-form">
    <header class="inline-form__header">
      <h4>{{ title }}</h4>
      <el-button text @click="$emit('cancel')">取消</el-button>
    </header>
    <div class="inline-form__body">
      <slot />
    </div>
    <footer class="inline-form__footer">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="loading" @click="$emit('submit')">提交</el-button>
    </footer>
  </div>
</template>

<style scoped>
.inline-form {
  animation: fade-in var(--duration-normal) var(--ease-default);
}

.inline-form__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-5);
}

.inline-form__header h4 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--text-primary);
}

.inline-form__body {
  margin-bottom: var(--sp-5);
}

.inline-form__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
  padding-top: var(--sp-4);
  border-top: 1px solid var(--border-light);
}
</style>
