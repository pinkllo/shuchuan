<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  value: number;
  label?: string;
  color?: string;
}>();

const clampedValue = computed(() => Math.min(100, Math.max(0, props.value)));
const barColor = computed(() => {
  if (props.color) return props.color;
  if (clampedValue.value >= 100) return 'var(--success)';
  return 'var(--accent)';
});
</script>

<template>
  <div class="progress-bar">
    <div class="progress-bar__track">
      <div
        class="progress-bar__fill"
        :style="{ width: `${clampedValue}%`, background: barColor }"
      />
    </div>
    <span class="progress-bar__label">{{ label ?? `${clampedValue}%` }}</span>
  </div>
</template>

<style scoped>
.progress-bar {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.progress-bar__track {
  flex: 1;
  height: 6px;
  background: var(--bg-hover);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--duration-fast) var(--ease-default);
}

.progress-bar__label {
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--text-tertiary);
  min-width: 36px;
  text-align: right;
}
</style>
