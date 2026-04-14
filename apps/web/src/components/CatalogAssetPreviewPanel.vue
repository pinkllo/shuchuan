<script setup lang="ts">
import { computed } from "vue";

import type { CatalogAssetPreviewItem } from "@/types/catalogAsset";
import {
  buildCatalogAssetPreviewMeta,
  formatCatalogAssetPreviewText
} from "@/utils/catalogAssetPreview";

const props = withDefaults(
  defineProps<{
    preview: CatalogAssetPreviewItem | null;
    imageUrl?: string | null;
    imageAlt?: string;
    loading?: boolean;
    error?: string | null;
    emptyText?: string;
  }>(),
  {
    imageUrl: null,
    imageAlt: "预览图片",
    loading: false,
    error: null,
    emptyText: "请选择文件查看预览"
  }
);

const previewMeta = computed(() => {
  if (!props.preview) {
    return [];
  }
  return buildCatalogAssetPreviewMeta(props.preview);
});

const previewText = computed(() => {
  if (!props.preview) {
    return props.emptyText;
  }
  return formatCatalogAssetPreviewText(props.preview.previewText);
});
</script>

<template>
  <section class="preview-panel">
    <header class="preview-panel__head">
      <div>
        <h4>{{ preview?.fileName ?? "目录文件预览" }}</h4>
        <p>显示文本样例与文件元信息，供页面按需接入。</p>
      </div>
    </header>

    <p v-if="loading" class="preview-panel__state">正在加载预览...</p>
    <p v-else-if="error" class="preview-panel__state preview-panel__state--error">{{ error }}</p>
    <div v-else-if="imageUrl" class="preview-panel__body">
      <div class="preview-panel__image-wrap">
        <img class="preview-panel__image" :src="imageUrl" :alt="imageAlt" />
      </div>
    </div>
    <div v-else-if="preview" class="preview-panel__body">
      <dl class="preview-panel__meta">
        <div v-for="item in previewMeta" :key="item.label" class="preview-panel__meta-item">
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
      <pre class="preview-panel__text">{{ previewText }}</pre>
    </div>
    <p v-else class="preview-panel__state">{{ previewText }}</p>
  </section>
</template>

<style scoped>
.preview-panel {
  display: grid;
  gap: 12px;
}

.preview-panel__head h4,
.preview-panel__head p,
.preview-panel__meta-item dd {
  margin: 0;
}

.preview-panel__head p,
.preview-panel__state,
.preview-panel__meta-item dt {
  color: var(--text-soft);
}

.preview-panel__body {
  display: grid;
  gap: 12px;
}

.preview-panel__meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin: 0;
}

.preview-panel__meta-item {
  padding: 12px;
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  background: var(--surface-strong);
}

.preview-panel__text {
  margin: 0;
  padding: 16px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--border-soft);
  white-space: pre-wrap;
  word-break: break-word;
}

.preview-panel__image-wrap {
  padding: 12px;
  border-radius: 18px;
  background: var(--surface-strong);
  border: 1px solid var(--border-soft);
}

.preview-panel__image {
  display: block;
  max-width: 100%;
  max-height: 360px;
  margin: 0 auto;
}

.preview-panel__state--error {
  color: var(--danger-strong);
}
</style>
