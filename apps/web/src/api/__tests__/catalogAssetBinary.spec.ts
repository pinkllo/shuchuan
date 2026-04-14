import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchCatalogAssetPreviewBinary } from "@/api/catalogAssets";

const fetchMock = vi.fn<typeof fetch>();

describe("catalog asset binary api", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads binary preview content with authorization", async () => {
    fetchMock.mockResolvedValue(
      new Response(new Uint8Array([1, 2, 3]), {
        status: 200,
        headers: { "content-type": "image/png" }
      })
    );

    const result = await fetchCatalogAssetPreviewBinary(7, 21, "token-123");

    const [url, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/catalogs/7/assets/21/preview-file");
    expect((request.headers as Record<string, string>).Authorization).toBe("Bearer token-123");
    expect(result.contentType).toBe("image/png");
    expect(result.blob).toBeInstanceOf(Blob);
  });
});
