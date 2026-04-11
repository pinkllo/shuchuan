<script setup lang="ts">
defineProps<{
  label: string;
  value: string;
  note: string;
  tone?: "jade" | "amber" | "slate";
}>();
</script>

<template>
  <article class="metric-card" :class="`metric-card--${tone ?? 'jade'}`">
    <p>{{ label }}</p>
    <strong>{{ value }}</strong>
    <span>{{ note }}</span>
  </article>
</template>

<style scoped>
.metric-card {
  padding: 22px;
  border-radius: 24px;
  min-height: 156px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 18px 38px rgba(12, 45, 61, 0.08);
}

.metric-card p,
.metric-card span {
  margin: 0;
}

.metric-card strong {
  font-size: clamp(28px, 4vw, 38px);
  line-height: 1;
}

.metric-card span {
  line-height: 1.6;
}

.metric-card--jade {
  background: linear-gradient(150deg, #f4fcf8, #dff2e8);
  color: #0f4d44;
}

.metric-card--amber {
  background: linear-gradient(150deg, #fff7ec, #ffe3bc);
  color: #8f4c16;
}

.metric-card--slate {
  background: linear-gradient(150deg, #eef7fa, #ddeef4);
  color: #124d63;
}
</style>
