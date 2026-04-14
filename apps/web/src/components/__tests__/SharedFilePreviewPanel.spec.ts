import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchBinaryMock = vi.fn();

vi.mock("@/stores/session", () => ({
  useSessionStore: () => ({
    accessToken: "token-123"
  })
}));

vi.mock("@/api/catalogAssets", () => ({
  fetchCatalogAssetPreview: vi.fn(),
  fetchCatalogAssetPreviewBinary: (...args: unknown[]) => fetchBinaryMock(...args)
}));

describe("SharedFilePreviewPanel", () => {
  beforeEach(() => {
    fetchBinaryMock.mockReset();
  });

  it("renders image preview for image assets", async () => {
    fetchBinaryMock.mockResolvedValue({
      blob: new Blob([new Uint8Array([1, 2, 3])], { type: "image/png" }),
      contentType: "image/png"
    });
    const originalCreateObjectUrl = URL.createObjectURL;
    const originalRevokeObjectUrl = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn(() => "blob:image-preview");
    URL.revokeObjectURL = vi.fn();

    const component = await import("@/components/SharedFilePreviewPanel.vue");
    const wrapper = mount(component.default, {
      props: {
        asset: {
          id: 21,
          catalogId: 7,
          uploadedBy: 2,
          fileName: "preview.png",
          filePath: "uploads/catalogs/7/preview.png",
          fileSize: 128,
          fileType: "image/png",
          uploadedAt: "2026-04-12T00:00:00Z"
        }
      }
    });

    await flushPromises();

    expect(fetchBinaryMock).toHaveBeenCalledWith(7, 21, "token-123");
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(wrapper.get("img").attributes("src")).toBe("blob:image-preview");

    URL.createObjectURL = originalCreateObjectUrl;
    URL.revokeObjectURL = originalRevokeObjectUrl;
  });
});
