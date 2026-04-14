<script setup lang="ts">
defineProps<{
  title: string;
  count?: number;
}>();
</script>

<template>
  <div class="kanban-col">
    <header class="kanban-col__header">
      <span class="kanban-col__title">{{ title }}</span>
      <span v-if="count !== undefined" class="kanban-col__count">{{ count }}</span>
    </header>
    <div class="kanban-col__body scrollable">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.kanban-col {
  display: flex;
  flex-direction: column;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.kanban-col__header {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--border-light);
}

.kanban-col__title {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.kanban-col__count {
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  color: var(--text-tertiary);
  background: var(--bg-hover);
  padding: 1px 8px;
  border-radius: var(--radius-full);
}

.kanban-col__body {
  flex: 1;
  padding: var(--sp-2);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  max-height: 480px;
}
</style>
