<script setup lang="ts">
defineEmits<{
  click: [];
}>();
</script>

<template>
  <article class="kanban-card" @click="$emit('click')">
    <slot />
  </article>
</template>

<style scoped>
.kanban-card {
  padding: var(--sp-3);
  border-radius: var(--radius-sm);
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: box-shadow var(--duration-fast) var(--ease-default),
              transform var(--duration-fast) var(--ease-default);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

.kanban-card:hover {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
}

.kanban-card :deep(strong) {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--text-primary);
  margin-bottom: 2px;
}

.kanban-card :deep(small) {
  display: block;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: var(--leading-normal);
}
</style>
