import { http } from "@/api/http";
import { buildApiUrl } from "@/api/http";
import type { CatalogAssetItem, CatalogAssetPreviewItem } from "@/types/catalogAsset";

interface BackendCatalogAsset {
  id: number;
  catalog_id: number;
  uploaded_by: number;
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
}

interface BackendCatalogAssetPreview {
  catalog_id: number;
  asset_id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  preview_text: string;
  preview_line_count: number;
  truncated: boolean;
}

export async function fetchCatalogAssets(catalogId: number, token: string): Promise<CatalogAssetItem[]> {
  const response = await http<BackendCatalogAsset[]>(`/api/catalogs/${catalogId}/assets`, { token });
  return response.map(mapCatalogAsset);
}

export async function appendCatalogAssets(
  catalogId: number,
  files: File[],
  token: string
): Promise<CatalogAssetItem[]> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const response = await http<BackendCatalogAsset[]>(`/api/catalogs/${catalogId}/assets`, {
    method: "POST",
    token,
    body: formData
  });
  return response.map(mapCatalogAsset);
}

export async function deleteCatalogAsset(catalogId: number, assetId: number, token: string): Promise<void> {
  await http<void>(`/api/catalogs/${catalogId}/assets/${assetId}`, {
    method: "DELETE",
    token
  });
}

export async function fetchCatalogAssetPreview(
  catalogId: number,
  assetId: number,
  token: string
): Promise<CatalogAssetPreviewItem> {
  const response = await http<BackendCatalogAssetPreview>(
    `/api/catalogs/${catalogId}/assets/${assetId}/preview`,
    { token }
  );
  return mapCatalogAssetPreview(response);
}

export async function fetchCatalogAssetPreviewBinary(
  catalogId: number,
  assetId: number,
  token: string
): Promise<{ blob: Blob; contentType: string }> {
  const response = await fetch(buildApiUrl(`/api/catalogs/${catalogId}/assets/${assetId}/preview-file`), {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  if (!response.ok) {
    throw new Error(await response.text() || "预览文件加载失败");
  }
  return {
    blob: await response.blob(),
    contentType: response.headers.get("content-type") ?? "application/octet-stream"
  };
}

function mapCatalogAsset(item: BackendCatalogAsset): CatalogAssetItem {
  return {
    id: item.id,
    catalogId: item.catalog_id,
    uploadedBy: item.uploaded_by,
    fileName: item.file_name,
    filePath: item.file_path,
    fileSize: item.file_size,
    fileType: item.file_type,
    uploadedAt: item.uploaded_at
  };
}

function mapCatalogAssetPreview(item: BackendCatalogAssetPreview): CatalogAssetPreviewItem {
  return {
    catalogId: item.catalog_id,
    assetId: item.asset_id,
    fileName: item.file_name,
    fileType: item.file_type,
    fileSize: item.file_size,
    uploadedAt: item.uploaded_at,
    previewText: item.preview_text,
    previewLineCount: item.preview_line_count,
    truncated: item.truncated
  };
}
