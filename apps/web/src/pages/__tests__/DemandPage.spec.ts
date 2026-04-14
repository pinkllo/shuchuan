import { computed, defineComponent, h, inject, provide, ref, watchEffect, type InjectionKey, type Ref } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CatalogItem } from "@/types/catalog";
import type { CatalogAssetItem } from "@/types/catalogAsset";
import type { DemandItem } from "@/types/demand";

const loadAllMock = vi.fn().mockResolvedValue(undefined);
const loadPublishedMock = vi.fn().mockResolvedValue(undefined);
const loadAssetsMock = vi.fn();
const submitMock = vi.fn().mockResolvedValue(undefined);
const approveMock = vi.fn().mockResolvedValue(undefined);

const catalogItems: CatalogItem[] = [
  {
    id: 7,
    providerId: 2,
    name: "课程论坛问答集",
    dataType: "text",
    granularity: "主题/帖子/回复",
    version: "v2026.04",
    fieldsDescription: "标题、正文、回复内容",
    scaleDescription: "约 12000 条",
    uploadMethod: "平台上传",
    sensitivityLevel: "internal",
    description: "教育问答语料",
    status: "published",
    assetCount: 2,
    createdAt: "2026-04-12T00:00:00Z"
  }
];

const catalogAssets: CatalogAssetItem[] = [
  {
    id: 11,
    catalogId: 7,
    uploadedBy: 2,
    fileName: "part-001.jsonl",
    filePath: "uploads/catalogs/7/part-001.jsonl",
    fileSize: 4096,
    fileType: "application/json",
    uploadedAt: "2026-04-12T00:00:00Z"
  }
];

const demandItems: DemandItem[] = [
  {
    id: 101,
    catalogId: 7,
    requesterId: 3,
    providerId: 2,
    title: "教育问答清洗需求",
    purpose: "构造训练样本",
    deliveryPlan: "2026-05-31",
    status: "data_uploaded",
    approvalNote: "通过",
    createdAt: "2026-04-12T00:00:00Z"
  }
];

const tableRowsKey: InjectionKey<Ref<Record<string, unknown>[]>> = Symbol("tableRows");

vi.mock("element-plus", () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  }
}));

vi.mock("@/api/http", () => ({
  getErrorMessage: (error: unknown) => String(error)
}));

vi.mock("@/stores/session", () => ({
  useSessionStore: () => ({
    accessToken: "token-123"
  })
}));

vi.mock("@/stores/demandStore", () => ({
  useDemandStore: () => ({
    items: demandItems,
    loading: false,
    loadAll: loadAllMock,
    submit: submitMock,
    approve: approveMock
  })
}));

vi.mock("@/stores/catalogStore", () => ({
  useCatalogStore: () => ({
    items: catalogItems,
    publishedItems: catalogItems,
    loadPublished: loadPublishedMock,
    loadMine: vi.fn(),
    loadAssets: loadAssetsMock,
    assetsForCatalog: (catalogId: number) => (catalogId === 7 ? catalogAssets : [])
  })
}));

vi.mock("@/composables/usePermission", () => ({
  usePermission: () => ({
    isProvider: computed(() => false),
    isAggregator: computed(() => true)
  })
}));

const StatusPillStub = defineComponent({
  name: "StatusPillStub",
  props: {
    label: {
      type: String,
      default: ""
    }
  },
  template: "<span>{{ label }}</span>"
});

const ElButtonStub = defineComponent({
  name: "ElButtonStub",
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ["click"],
  template: "<button :disabled='disabled' @click=\"$emit('click')\"><slot /></button>"
});

const ElDialogStub = defineComponent({
  name: "ElDialogStub",
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ""
    }
  },
  template: "<section v-if='modelValue'><h4>{{ title }}</h4><slot /><slot name='footer' /></section>"
});

const ElFormStub = defineComponent({
  name: "ElFormStub",
  template: "<form><slot /></form>"
});

const ElFormItemStub = defineComponent({
  name: "ElFormItemStub",
  props: {
    label: {
      type: String,
      default: ""
    }
  },
  template: "<label><span>{{ label }}</span><slot /></label>"
});

const ElInputStub = defineComponent({
  name: "ElInputStub",
  props: {
    modelValue: {
      type: String,
      default: ""
    }
  },
  emits: ["update:modelValue"],
  template: "<input :value='modelValue' @input=\"$emit('update:modelValue', $event.target.value)\" />"
});

const ElSelectStub = defineComponent({
  name: "ElSelectStub",
  template: "<div class='select-stub'><slot /></div>"
});

const ElOptionStub = defineComponent({
  name: "ElOptionStub",
  props: {
    label: {
      type: String,
      default: ""
    }
  },
  template: "<div class='option-stub'>{{ label }}<slot /></div>"
});

const ElTableStub = defineComponent({
  name: "ElTableStub",
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  setup(props, { slots }) {
    const rows = ref(props.data as Record<string, unknown>[]);
    watchEffect(() => {
      rows.value = props.data as Record<string, unknown>[];
    });
    provide(tableRowsKey, rows);
    return () => h("div", { class: "table-stub" }, slots.default ? slots.default() : []);
  }
});

const ElTableColumnStub = defineComponent({
  name: "ElTableColumnStub",
  props: {
    prop: {
      type: String,
      default: ""
    },
    label: {
      type: String,
      default: ""
    }
  },
  setup(props, { slots }) {
    const rows = inject(tableRowsKey, ref([] as Record<string, unknown>[]));
    return () =>
      h(
        "div",
        { class: "column-stub" },
        rows.value.map((row, index) =>
          h(
            "div",
            {
              class: "cell-stub",
              "data-label": props.label,
              key: `${props.label}-${index}`
            },
            slots.default ? slots.default({ row, $index: index }) : String(row[props.prop] ?? "")
          )
        )
      );
  }
});

const SharedFilePreviewPanelStub = defineComponent({
  name: "SharedFilePreviewPanel",
  props: {
    asset: {
      type: Object,
      default: null
    },
    title: {
      type: String,
      default: ""
    }
  },
  template: "<div data-test='preview-panel'>{{ title }} / {{ asset?.fileName }}</div>"
});

describe("DemandPage", () => {
  beforeEach(() => {
    loadAllMock.mockClear();
    loadPublishedMock.mockClear();
    loadAssetsMock.mockClear();
    loadAssetsMock.mockResolvedValue(catalogAssets);
    submitMock.mockClear();
    approveMock.mockClear();
  });

  it("shows richer catalog information in the demand flow", async () => {
    const component = await import("@/pages/DemandPage.vue");
    const wrapper = mount(component.default, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          StatusPill: StatusPillStub,
          ElButton: ElButtonStub,
          ElDialog: ElDialogStub,
          ElForm: ElFormStub,
          ElFormItem: ElFormItemStub,
          ElInput: ElInputStub,
          ElSelect: ElSelectStub,
          ElOption: ElOptionStub,
          ElTable: ElTableStub,
          ElTableColumn: ElTableColumnStub,
          SharedFilePreviewPanel: SharedFilePreviewPanelStub
        }
      }
    });

    const viewModel = wrapper.vm as unknown as {
      createDialog: boolean;
      createForm: {
        catalogId: number;
      };
    };
    viewModel.createDialog = true;
    viewModel.createForm.catalogId = 7;
    await flushPromises();

    expect(wrapper.text()).toContain("课程论坛问答集");
    expect(wrapper.text()).toContain("v2026.04");
    expect(wrapper.text()).toContain("text");
    expect(wrapper.text()).toContain("主题/帖子/回复");
    expect(wrapper.text()).not.toContain("目录 #7");
  });

  it("shows a preview action for catalog assets and wires the selected file into the shared preview panel", async () => {
    const component = await import("@/pages/DemandPage.vue");
    const wrapper = mount(component.default, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          StatusPill: StatusPillStub,
          ElButton: ElButtonStub,
          ElDialog: ElDialogStub,
          ElForm: ElFormStub,
          ElFormItem: ElFormItemStub,
          ElInput: ElInputStub,
          ElSelect: ElSelectStub,
          ElOption: ElOptionStub,
          ElTable: ElTableStub,
          ElTableColumn: ElTableColumnStub,
          SharedFilePreviewPanel: SharedFilePreviewPanelStub
        }
      }
    });

    const viewButton = wrapper.findAll("button").find((item) => item.text() === "查看目录文件");
    await viewButton?.trigger("click");
    await flushPromises();

    expect(loadAssetsMock).toHaveBeenCalledWith(7, "token-123");
    expect(wrapper.text()).toContain("目录文件预览");
    expect(wrapper.text()).toContain("part-001.jsonl");

    const previewButton = wrapper.findAll("button").find((item) => item.text() === "预览");
    expect(previewButton).toBeDefined();
  });
});
