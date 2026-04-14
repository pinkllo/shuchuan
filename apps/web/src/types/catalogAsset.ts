export interface CatalogAssetItem {
  id: number;
  catalogId: number;
  uploadedBy: number;
  fileName: string;
  filePath: string;
  fileSize: number;
  fileType: string;
  uploadedAt: string;
}

export interface CatalogAssetPreviewItem {
  catalogId: number;
  assetId: number;
  fileName: string;
  fileType: string;
  fileSize: number;
  uploadedAt: string;
  previewText: string;
  previewLineCount: number;
  truncated: boolean;
}

export interface CatalogAssetPreviewMetaItem {
  label: string;
  value: string;
}
