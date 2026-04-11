<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppShell from "@/layout/AppShell.vue";

const route = useRoute();
const useShell = computed(() => route.meta.shell !== false);
</script>

<template>
  <AppShell v-if="useShell" />
  <router-view v-else />
</template>
