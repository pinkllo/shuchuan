import type { CatalogItem } from "@/types/catalog";
import type { CatalogAssetItem } from "@/types/catalogAsset";
import type { DemandItem } from "@/types/demand";

import { formatCatalogAssetFileSize } from "@/utils/catalogAssetPreview";

export function buildCatalogOptionLabel(
  catalog: Pick<CatalogItem, "name" | "version" | "dataType" | "granularity" | "assetCount">
): string {
  return `${catalog.name} / ${catalog.version} / ${catalog.dataType} / ${catalog.granularity} / ${catalog.assetCount}个文件`;
}

export function buildDemandOptionLabel(
  demand: Pick<DemandItem, "id" | "title">,
  catalog: Pick<CatalogItem, "name" | "version"> | null
): string {
  if (!catalog) {
    return `需求 #${demand.id} / ${demand.title}`;
  }
  return `${demand.title} / ${catalog.name} ${catalog.version}`;
}

export function buildCatalogAssetOptionLabel(
  asset: Pick<CatalogAssetItem, "fileName" | "fileType" | "fileSize">
): string {
  return `${asset.fileName} / ${asset.fileType} / ${formatCatalogAssetFileSize(asset.fileSize)}`;
}

export function findCatalogById(
  catalogs: readonly CatalogItem[],
  catalogId: number
): CatalogItem | null {
  return catalogs.find((item) => item.id === catalogId) ?? null;
}
