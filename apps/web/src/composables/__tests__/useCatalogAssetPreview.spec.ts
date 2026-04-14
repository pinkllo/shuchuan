import { defineComponent } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import { useCatalogAssetPreview } from "@/composables/useCatalogAssetPreview";

const Harness = defineComponent({
  name: "CatalogAssetPreviewHarness",
  props: {
    loadPreview: {
      type: Function,
      required: true
    }
  },
  setup(props) {
    return useCatalogAssetPreview({
      loadPreview: props.loadPreview as (
        catalogId: number,
        assetId: number,
        token: string
      ) => Promise<unknown>
    });
  },
  template: "<div />"
});

describe("useCatalogAssetPreview", () => {
  it("loads preview data and exposes preview metadata", async () => {
    const loadPreview = vi.fn().mockResolvedValue({
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

    const wrapper = mount(Harness, {
      props: {
        loadPreview
      }
    });

    const viewModel = wrapper.vm as unknown as {
      loading: boolean;
      error: string | null;
      previewText: string;
      previewMeta: Array<{ label: string; value: string }>;
      load: (catalogId: number, assetId: number, token: string) => Promise<void>;
      reset: () => void;
    };

    const pending = viewModel.load(7, 21, "token-123");
    expect(viewModel.loading).toBe(true);

    await pending;
    await flushPromises();

    expect(loadPreview).toHaveBeenCalledWith(7, 21, "token-123");
    expect(viewModel.loading).toBe(false);
    expect(viewModel.error).toBeNull();
    expect(viewModel.previewText).toBe("{\"question\":\"Q1\"}");
    expect(viewModel.previewMeta).toContainEqual({ label: "预览状态", value: "已截断" });

    viewModel.reset();
    expect(viewModel.previewText).toBe("暂无可展示的文本样例");
    expect(viewModel.previewMeta).toEqual([]);
  });
});
