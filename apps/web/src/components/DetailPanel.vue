<script setup lang="ts">
</script>

<template>
  <div class="detail-panel">
    <header v-if="$slots.header" class="detail-panel__header">
      <slot name="header" />
    </header>
    <div class="detail-panel__body scrollable">
      <slot />
    </div>
    <footer v-if="$slots.actions" class="detail-panel__actions">
      <slot name="actions" />
    </footer>
  </div>
</template>

<style scoped>
.detail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.detail-panel__header {
  padding-bottom: var(--sp-4);
  margin-bottom: var(--sp-4);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.detail-panel__body {
  flex: 1;
  min-height: 0;
}

.detail-panel__actions {
  padding-top: var(--sp-4);
  margin-top: var(--sp-4);
  border-top: 1px solid var(--border-light);
  display: flex;
  gap: var(--sp-2);
  justify-content: flex-end;
  flex-shrink: 0;
}
</style>
