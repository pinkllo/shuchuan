import { computed, ref } from "vue";

import { fetchCatalogAssetPreview } from "@/api/catalogAssets";
import { getErrorMessage } from "@/api/http";
import type { CatalogAssetPreviewItem, CatalogAssetPreviewMetaItem } from "@/types/catalogAsset";
import {
  buildCatalogAssetPreviewMeta,
  formatCatalogAssetPreviewText
} from "@/utils/catalogAssetPreview";

type CatalogAssetPreviewLoader = (
  catalogId: number,
  assetId: number,
  token: string
) => Promise<CatalogAssetPreviewItem>;

interface UseCatalogAssetPreviewOptions {
  loadPreview?: CatalogAssetPreviewLoader;
}

export function useCatalogAssetPreview(options: UseCatalogAssetPreviewOptions = {}) {
  const preview = ref<CatalogAssetPreviewItem | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const loadPreview = options.loadPreview ?? fetchCatalogAssetPreview;

  const previewText = computed(() => formatCatalogAssetPreviewText(preview.value?.previewText ?? ""));
  const previewMeta = computed<CatalogAssetPreviewMetaItem[]>(() => {
    if (!preview.value) {
      return [];
    }
    return buildCatalogAssetPreviewMeta(preview.value);
  });

  async function load(catalogId: number, assetId: number, token: string) {
    loading.value = true;
    error.value = null;
    try {
      preview.value = await loadPreview(catalogId, assetId, token);
    } catch (nextError) {
      preview.value = null;
      error.value = getErrorMessage(nextError);
      throw nextError;
    } finally {
      loading.value = false;
    }
  }

  function reset() {
    preview.value = null;
    loading.value = false;
    error.value = null;
  }

  return {
    error,
    loading,
    preview,
    previewMeta,
    previewText,
    load,
    reset
  };
}
