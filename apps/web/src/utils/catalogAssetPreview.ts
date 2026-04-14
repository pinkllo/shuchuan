import type { CatalogAssetPreviewItem, CatalogAssetPreviewMetaItem } from "@/types/catalogAsset";

const BYTES_PER_KB = 1024;
const BYTES_PER_MB = BYTES_PER_KB * 1024;

export function buildCatalogAssetPreviewMeta(
  preview: CatalogAssetPreviewItem
): CatalogAssetPreviewMetaItem[] {
  return [
    { label: "文件类型", value: preview.fileType },
    { label: "文件大小", value: formatCatalogAssetFileSize(preview.fileSize) },
    { label: "上传时间", value: preview.uploadedAt },
    { label: "预览行数", value: `${preview.previewLineCount} 行` },
    { label: "预览状态", value: preview.truncated ? "已截断" : "完整内容" }
  ];
}

export function formatCatalogAssetPreviewText(previewText: string): string {
  return previewText.trim() ? previewText : "暂无可展示的文本样例";
}

export function formatCatalogAssetFileSize(fileSize: number): string {
  if (fileSize >= BYTES_PER_MB) {
    return `${(fileSize / BYTES_PER_MB).toFixed(1)} MB`;
  }
  if (fileSize >= BYTES_PER_KB) {
    return `${(fileSize / BYTES_PER_KB).toFixed(1)} KB`;
  }
  return `${fileSize} B`;
}
