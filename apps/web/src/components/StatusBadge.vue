<script setup lang="ts">
defineProps<{
  label: string;
  tone?: 'success' | 'warning' | 'danger' | 'info' | 'muted';
}>();
</script>

<template>
  <span class="status-badge" :class="`status-badge--${tone ?? 'muted'}`">
    <span class="status-badge__dot" />
    <span class="status-badge__label">{{ label }}</span>
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  line-height: 1.6;
  white-space: nowrap;
}

.status-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-badge--success { background: var(--success-light); color: var(--success); }
.status-badge--success .status-badge__dot { background: var(--success); }

.status-badge--warning { background: var(--warning-light); color: var(--warning); }
.status-badge--warning .status-badge__dot { background: var(--warning); }

.status-badge--danger { background: var(--danger-light); color: var(--danger); }
.status-badge--danger .status-badge__dot { background: var(--danger); }

.status-badge--info { background: var(--info-light); color: var(--info); }
.status-badge--info .status-badge__dot { background: var(--info); }

.status-badge--muted { background: var(--bg-hover); color: var(--text-secondary); }
.status-badge--muted .status-badge__dot { background: var(--text-tertiary); }
</style>
