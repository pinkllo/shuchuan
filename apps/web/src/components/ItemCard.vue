<script setup lang="ts">
defineProps<{
  selected?: boolean;
}>();

defineEmits<{
  click: [];
}>();
</script>

<template>
  <article
    class="item-card"
    :class="{ 'item-card--selected': selected }"
    @click="$emit('click')"
  >
    <slot />
  </article>
</template>

<style scoped>
.item-card {
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default),
              border-color var(--duration-fast) var(--ease-default);
  border: 1px solid transparent;
  margin-bottom: var(--sp-1);
}

.item-card:hover {
  background: var(--bg-hover);
}

.item-card--selected {
  background: var(--bg-active);
  border-color: var(--accent);
  border-left: 3px solid var(--accent);
}
</style>
