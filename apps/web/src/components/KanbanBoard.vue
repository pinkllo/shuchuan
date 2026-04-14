<template>
  <div class="kanban-board">
    <slot />
  </div>
</template>

<style scoped>
.kanban-board {
  display: flex;
  gap: var(--sp-4);
  min-height: 320px;
}

.kanban-board > :deep(*) {
  flex: 1;
  min-width: 0;
}

@media (max-width: 768px) {
  .kanban-board {
    flex-direction: column;
  }
}
</style>
