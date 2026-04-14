<script setup lang="ts">
defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__icon">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" stroke-width="1.5" fill="none" />
        <path d="M6 18h36" stroke="currentColor" stroke-width="1.5" />
        <circle cx="12" cy="14" r="1.5" fill="currentColor" />
        <circle cx="17" cy="14" r="1.5" fill="currentColor" />
        <circle cx="22" cy="14" r="1.5" fill="currentColor" />
        <rect x="16" y="24" width="16" height="2" rx="1" fill="currentColor" opacity="0.4" />
        <rect x="20" y="29" width="8" height="2" rx="1" fill="currentColor" opacity="0.3" />
      </svg>
    </div>
    <h4 class="empty-state__title">{{ title }}</h4>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--sp-12) var(--sp-6);
  text-align: center;
  min-height: 240px;
}

.empty-state__icon {
  color: var(--text-tertiary);
  margin-bottom: var(--sp-4);
  opacity: 0.6;
}

.empty-state__title {
  margin: 0 0 var(--sp-2);
  font-size: var(--text-md);
  font-weight: var(--weight-medium);
  color: var(--text-secondary);
}

.empty-state__desc {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  max-width: 320px;
  line-height: var(--leading-relaxed);
}
</style>
