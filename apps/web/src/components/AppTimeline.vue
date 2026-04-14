<script setup lang="ts">
export interface TimelineItem {
  time: string;
  content: string;
  type?: 'success' | 'warning' | 'danger' | 'info' | 'default';
}

defineProps<{
  items: TimelineItem[];
}>();
</script>

<template>
  <div class="timeline">
    <div v-for="(item, i) in items" :key="i" class="timeline__item">
      <div class="timeline__rail">
        <span class="timeline__dot" :class="`timeline__dot--${item.type ?? 'default'}`" />
        <span v-if="i < items.length - 1" class="timeline__line" />
      </div>
      <div class="timeline__body">
        <span class="timeline__time">{{ item.time }}</span>
        <span class="timeline__content">{{ item.content }}</span>
      </div>
    </div>
    <div v-if="items.length === 0" class="timeline__empty">暂无活动记录</div>
  </div>
</template>

<style scoped>
.timeline {
  display: flex;
  flex-direction: column;
}

.timeline__item {
  display: flex;
  gap: var(--sp-3);
  min-height: 48px;
}

.timeline__rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
  padding-top: 4px;
}

.timeline__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline__dot--default { background: var(--border); }
.timeline__dot--success { background: var(--success); }
.timeline__dot--warning { background: var(--warning); }
.timeline__dot--danger { background: var(--danger); }
.timeline__dot--info { background: var(--accent); }

.timeline__line {
  flex: 1;
  width: 1px;
  background: var(--border-light);
  margin: 4px 0;
}

.timeline__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: var(--sp-3);
}

.timeline__time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: var(--weight-medium);
}

.timeline__content {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
}

.timeline__empty {
  padding: var(--sp-6);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}
</style>
