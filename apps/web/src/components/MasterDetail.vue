<script setup lang="ts">
import EmptyState from './EmptyState.vue';

defineProps<{
  hasSelection: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
}>();
</script>

<template>
  <div class="master-detail">
    <aside class="master-detail__list scrollable">
      <slot name="list" />
    </aside>
    <div class="master-detail__divider" />
    <section class="master-detail__detail scrollable">
      <slot v-if="hasSelection" name="detail" />
      <EmptyState
        v-else
        :title="emptyTitle ?? '选择一个项目'"
        :description="emptyDescription ?? '从左侧列表中选择一个项目以查看详情。'"
      />
    </section>
  </div>
</template>

<style scoped>
.master-detail {
  display: flex;
  height: calc(100vh - var(--nav-height) - 48px);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.master-detail__list {
  width: var(--list-width);
  flex-shrink: 0;
  padding: var(--sp-4);
  border-right: none;
}

.master-detail__divider {
  width: 1px;
  background: var(--border);
  flex-shrink: 0;
}

.master-detail__detail {
  flex: 1;
  min-width: 0;
  padding: var(--sp-6);
}

@media (max-width: 768px) {
  .master-detail {
    flex-direction: column;
    height: auto;
  }

  .master-detail__list {
    width: 100%;
    max-height: 40vh;
  }

  .master-detail__divider {
    width: 100%;
    height: 1px;
  }

  .master-detail__detail {
    min-height: 50vh;
  }
}
</style>
