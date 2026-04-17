<script setup lang="ts">
defineEmits<{
  click: [];
}>();
</script>

<template>
  <article 
    class="p-3 rounded-md bg-white border border-gray-100 cursor-pointer text-sm leading-normal transition-all duration-150 ease-out hover:shadow-sm hover:border-gray-200 hover:-translate-y-[1px] [&_strong]:block [&_strong]:text-sm [&_strong]:font-medium [&_strong]:text-gray-900 [&_strong]:mb-0.5 [&_small]:block [&_small]:text-xs [&_small]:text-gray-400 [&_small]:leading-normal" 
    @click="$emit('click')"
  >
    <slot />
  </article>
</template>
