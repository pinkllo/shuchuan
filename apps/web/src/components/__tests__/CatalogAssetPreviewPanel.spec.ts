import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CatalogAssetPreviewPanel from "@/components/CatalogAssetPreviewPanel.vue";

describe("CatalogAssetPreviewPanel", () => {
  it("renders preview text and metadata", () => {
    const wrapper = mount(CatalogAssetPreviewPanel, {
      props: {
        preview: {
          catalogId: 7,
          assetId: 21,
          fileName: "part-01.jsonl",
          fileType: "application/json",
          fileSize: 2048,
          uploadedAt: "2026-04-12T00:00:00Z",
          previewText: "{\"question\":\"Q1\"}",
          previewLineCount: 12,
          truncated: true
        },
        loading: false,
        error: null
      }
    });

    expect(wrapper.text()).toContain("part-01.jsonl");
    expect(wrapper.text()).toContain("application/json");
    expect(wrapper.text()).toContain("2.0 KB");
    expect(wrapper.text()).toContain("12 行");
    expect(wrapper.text()).toContain("已截断");
    expect(wrapper.text()).toContain("{\"question\":\"Q1\"}");
  });

  it("renders image preview when image url is provided", () => {
    const wrapper = mount(CatalogAssetPreviewPanel, {
      props: {
        preview: null,
        imageUrl: "blob:http://localhost/image-preview",
        imageAlt: "sample-image",
        loading: false,
        error: null
      }
    });

    const image = wrapper.get("img");
    expect(image.attributes("src")).toBe("blob:http://localhost/image-preview");
    expect(image.attributes("alt")).toBe("sample-image");
  });
});
