<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { fetchCatalogAssetPreviewBinary } from "@/api/catalogAssets";
import CatalogAssetPreviewPanel from "@/components/CatalogAssetPreviewPanel.vue";
import { useCatalogAssetPreview } from "@/composables/useCatalogAssetPreview";
import { useSessionStore } from "@/stores/session";
import type { CatalogAssetItem } from "@/types/catalogAsset";

const props = withDefaults(
  defineProps<{
    asset: CatalogAssetItem | null;
    title?: string;
  }>(),
  {
    title: "目录文件预览"
  }
);

const sessionStore = useSessionStore();
const previewState = useCatalogAssetPreview();
const imageUrl = ref<string | null>(null);
const isImageAsset = computed(() => props.asset?.fileType.startsWith("image/") ?? false);
const preview = computed(() => previewState.preview.value);
const loading = computed(() => previewState.loading.value);
const error = computed(() => previewState.error.value);

watch(
  () => [props.asset, sessionStore.accessToken] as const,
  async ([asset, token]) => {
    if (!asset || !token) {
      resetPreview();
      return;
    }
    if (isImageAsset.value) {
      await loadImagePreview(asset, token);
      return;
    }
    imageUrl.value = null;
    try {
      await previewState.load(asset.catalogId, asset.id, token);
    } catch {}
  },
  { immediate: true }
);

onBeforeUnmount(revokeImageUrl);

async function loadImagePreview(asset: CatalogAssetItem, token: string) {
  previewState.reset();
  revokeImageUrl();
  try {
    const result = await fetchCatalogAssetPreviewBinary(asset.catalogId, asset.id, token);
    imageUrl.value = URL.createObjectURL(result.blob);
  } catch {
    imageUrl.value = null;
  }
}

function resetPreview() {
  previewState.reset();
  revokeImageUrl();
}

function revokeImageUrl() {
  if (!imageUrl.value) {
    return;
  }
  URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = null;
}
</script>

<template>
  <section class="shared-preview">
    <header class="shared-preview__head">
      <h4>{{ title }}</h4>
      <p>{{ asset ? `当前文件：${asset.fileName}` : "请选择文件查看样例内容" }}</p>
    </header>
    <CatalogAssetPreviewPanel
      :preview="preview"
      :image-url="imageUrl"
      :image-alt="asset?.fileName ?? '预览图片'"
      :loading="loading"
      :error="error"
    />
  </section>
</template>

<style scoped>
.shared-preview {
  display: grid;
  gap: 12px;
}

.shared-preview__head h4,
.shared-preview__head p {
  margin: 0;
}

.shared-preview__head p {
  color: var(--text-soft);
}
</style>
