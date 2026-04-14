import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchCatalogAssetPreview } from "@/api/catalogAssets";

const fetchMock = vi.fn<typeof fetch>();

describe("catalog asset api", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads a catalog asset preview and maps preview metadata", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          catalog_id: 7,
          asset_id: 21,
          file_name: "part-01.jsonl",
          file_type: "application/json",
          file_size: 2048,
          uploaded_at: "2026-04-12T00:00:00Z",
          preview_text: "{\"question\":\"Q1\"}\n{\"question\":\"Q2\"}",
          preview_line_count: 2,
          truncated: true
        }),
        {
          status: 200,
          headers: { "content-type": "application/json" }
        }
      )
    );

    const preview = await fetchCatalogAssetPreview(7, 21, "token-123");

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/catalogs/7/assets/21/preview");
    expect((request.headers as Headers).get("Authorization")).toBe("Bearer token-123");
    expect(preview).toEqual({
      catalogId: 7,
      assetId: 21,
      fileName: "part-01.jsonl",
      fileType: "application/json",
      fileSize: 2048,
      uploadedAt: "2026-04-12T00:00:00Z",
      previewText: "{\"question\":\"Q1\"}\n{\"question\":\"Q2\"}",
      previewLineCount: 2,
      truncated: true
    });
  });
});
