<script setup lang="ts">
defineProps<{
  title: string;
  count?: number;
}>();
</script>

<template>
  <div class="flex flex-col bg-gray-50/50 rounded-lg overflow-hidden flex-1 min-w-0 border border-gray-200">
    <header class="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-gray-50/80">
      <span class="text-xs font-medium text-gray-500 tracking-wider">{{ title }}</span>
      <span v-if="count !== undefined" class="text-[11px] font-semibold text-gray-500 bg-gray-200/50 px-2 py-0.5 rounded-full">{{ count }}</span>
    </header>
    <div class="flex-1 p-3 flex flex-col gap-2.5 max-h-[480px] overflow-y-auto overflow-x-hidden relative custom-scrollbar">
      <slot />
    </div>
  </div>
</template>
