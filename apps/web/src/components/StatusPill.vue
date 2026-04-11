<script setup lang="ts">
defineProps<{
  label: string;
  tone?: "good" | "warn" | "info" | "danger";
}>();
</script>

<template>
  <span class="status-pill" :class="`status-pill--${tone ?? 'info'}`">
    {{ label }}
  </span>
</template>

<style scoped>
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.status-pill--good {
  background: rgba(33, 145, 114, 0.16);
  color: #14674f;
}

.status-pill--warn {
  background: rgba(234, 140, 58, 0.18);
  color: #8b4a17;
}

.status-pill--info {
  background: rgba(18, 92, 122, 0.12);
  color: #125c7a;
}

.status-pill--danger {
  background: rgba(196, 67, 67, 0.14);
  color: #9f2c2c;
}
</style>
