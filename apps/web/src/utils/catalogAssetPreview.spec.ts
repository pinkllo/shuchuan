import { describe, expect, it } from "vitest";

import {
  buildCatalogAssetPreviewMeta,
  formatCatalogAssetFileSize,
  formatCatalogAssetPreviewText
} from "@/utils/catalogAssetPreview";

describe("catalogAssetPreview utils", () => {
  it("builds display metadata for a preview payload", () => {
    const meta = buildCatalogAssetPreviewMeta({
      catalogId: 7,
      assetId: 21,
      fileName: "part-01.jsonl",
      fileType: "application/json",
      fileSize: 2048,
      uploadedAt: "2026-04-12T00:00:00Z",
      previewText: "{\"question\":\"Q1\"}",
      previewLineCount: 12,
      truncated: true
    });

    expect(meta).toEqual([
      { label: "文件类型", value: "application/json" },
      { label: "文件大小", value: "2.0 KB" },
      { label: "上传时间", value: "2026-04-12T00:00:00Z" },
      { label: "预览行数", value: "12 行" },
      { label: "预览状态", value: "已截断" }
    ]);
  });

  it("returns a readable fallback when preview text is empty", () => {
    expect(formatCatalogAssetPreviewText("")).toBe("暂无可展示的文本样例");
    expect(formatCatalogAssetPreviewText("line 1\nline 2")).toBe("line 1\nline 2");
  });

  it("formats file sizes for selection summaries", () => {
    expect(formatCatalogAssetFileSize(128)).toBe("128 B");
    expect(formatCatalogAssetFileSize(2048)).toBe("2.0 KB");
  });
});
