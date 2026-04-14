import { defineComponent, nextTick } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const loadAllDemandsMock = vi.fn().mockResolvedValue(undefined);
const loadPublishedCatalogsMock = vi.fn().mockResolvedValue(undefined);
const loadAssetsMock = vi.fn().mockImplementation((catalogId: number) =>
  Promise.resolve(
    catalogId === 7
      ? [
          {
            id: 11,
            catalogId: 7,
            uploadedBy: 2,
            fileName: "a.jsonl",
            filePath: "uploads/catalogs/7/a.jsonl",
            fileSize: 128,
            fileType: "application/json",
            uploadedAt: "2026-04-12T00:00:00Z"
          }
        ]
      : [
          {
            id: 21,
            catalogId: 8,
            uploadedBy: 2,
            fileName: "b.jsonl",
            filePath: "uploads/catalogs/8/b.jsonl",
            fileSize: 128,
            fileType: "application/json",
            uploadedAt: "2026-04-12T00:00:00Z"
          }
        ]
  )
);
const loadAllTasksMock = vi.fn().mockResolvedValue(undefined);
const submitTaskMock = vi.fn().mockResolvedValue(undefined);

const catalogItems = [
  {
    id: 7,
    providerId: 2,
    name: "语料目录A",
    dataType: "text",
    granularity: "主题/帖子",
    version: "v2026.04",
    fieldsDescription: "标题、正文",
    scaleDescription: "1.2 万条",
    uploadMethod: "平台上传",
    sensitivityLevel: "internal",
    description: "用于处理页摘要测试",
    status: "published" as const,
    assetCount: 2,
    createdAt: "2026-04-12T00:00:00Z"
  },
  {
    id: 8,
    providerId: 2,
    name: "语料目录B",
    dataType: "image",
    granularity: "图片/标注",
    version: "v2026.05",
    fieldsDescription: "路径、标签",
    scaleDescription: "4200 条",
    uploadMethod: "接口同步",
    sensitivityLevel: "internal",
    description: "用于需求切换测试",
    status: "published" as const,
    assetCount: 1,
    createdAt: "2026-04-12T00:00:00Z"
  }
];

const demandItems = [
  {
    id: 1,
    catalogId: 7,
    requesterId: 3,
    providerId: 2,
    title: "需求一",
    purpose: "用途一",
    deliveryPlan: "2026-05-31",
    status: "data_uploaded" as const,
    approvalNote: "通过",
    createdAt: "2026-04-12T00:00:00Z"
  },
  {
    id: 2,
    catalogId: 8,
    requesterId: 3,
    providerId: 2,
    title: "需求二",
    purpose: "用途二",
    deliveryPlan: "2026-05-31",
    status: "data_uploaded" as const,
    approvalNote: "通过",
    createdAt: "2026-04-12T00:00:00Z"
  }
];

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

vi.mock("@/stores/capabilityStore", () => ({
  useCapabilityStore: () => ({
    capabilities: [],
    selectableCapabilities: [{ id: "instruction", name: "指令生成", description: "desc" }]
  })
}));

vi.mock("@/stores/demandStore", () => ({
  useDemandStore: () => ({
    items: demandItems,
    loading: false,
    loadAll: loadAllDemandsMock
  })
}));

vi.mock("@/stores/catalogStore", () => ({
  useCatalogStore: () => ({
    items: catalogItems,
    publishedItems: catalogItems,
    loadPublished: loadPublishedCatalogsMock,
    loadAssets: loadAssetsMock,
    assetsForCatalog: (catalogId: number) =>
      catalogId === 7
        ? [
            {
              id: 11,
              catalogId: 7,
              uploadedBy: 2,
              fileName: "a.jsonl",
              filePath: "uploads/catalogs/7/a.jsonl",
              fileSize: 128,
              fileType: "application/json",
              uploadedAt: "2026-04-12T00:00:00Z"
            }
          ]
        : [
            {
              id: 21,
              catalogId: 8,
              uploadedBy: 2,
              fileName: "b.jsonl",
              filePath: "uploads/catalogs/8/b.jsonl",
              fileSize: 128,
              fileType: "application/json",
              uploadedAt: "2026-04-12T00:00:00Z"
            }
          ]
  })
}));

vi.mock("@/stores/taskStore", () => ({
  useTaskStore: () => ({
    items: [],
    loading: false,
    loadAll: loadAllTasksMock,
    submit: submitTaskMock,
    updateStatus: vi.fn(),
    registerArtifact: vi.fn()
  })
}));

const StatusPillStub = defineComponent({
  name: "StatusPillStub",
  template: "<span><slot /></span>"
});

const ElDialogStub = defineComponent({
  name: "ElDialogStub",
  template: "<div><slot /><slot name='footer' /></div>"
});

const ElFormStub = defineComponent({
  name: "ElFormStub",
  template: "<form><slot /></form>"
});

const ElFormItemStub = defineComponent({
  name: "ElFormItemStub",
  template: "<div><slot /></div>"
});

const ElTableStub = defineComponent({
  name: "ElTableStub",
  template: "<div><slot /></div>"
});

const ElTableColumnStub = defineComponent({
  name: "ElTableColumnStub",
  template: "<div><slot :row=\"{ id: 1, demandId: 1, inputAssetIds: [] }\" /></div>"
});

const ElSelectStub = defineComponent({
  name: "ElSelectStub",
  props: {
    modelValue: {
      type: [Number, String, Array],
      default: undefined
    }
  },
  emits: ["update:modelValue"],
  template: "<div><slot /></div>"
});

const ElOptionStub = defineComponent({
  name: "ElOptionStub",
  props: {
    label: {
      type: String,
      default: ""
    },
    value: {
      type: [Number, String, Array],
      default: undefined
    }
  },
  template: "<div class='option-stub'>{{ label }}</div>"
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
  template: `<button :disabled="disabled" @click="$emit('click')"><slot /></button>`
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
  template: "<div data-test='preview-panel'>预览: {{ title }} / {{ asset?.fileName }}</div>"
});

describe("ProcessingPage", () => {
  beforeEach(() => {
    loadAllDemandsMock.mockClear();
    loadPublishedCatalogsMock.mockClear();
    loadAssetsMock.mockClear();
    loadAssetsMock.mockImplementation((catalogId: number) =>
      Promise.resolve(
        catalogId === 7
          ? [
              {
                id: 11,
                catalogId: 7,
                uploadedBy: 2,
                fileName: "a.jsonl",
                filePath: "uploads/catalogs/7/a.jsonl",
                fileSize: 128,
                fileType: "application/json",
                uploadedAt: "2026-04-12T00:00:00Z"
              }
            ]
          : [
              {
                id: 21,
                catalogId: 8,
                uploadedBy: 2,
                fileName: "b.jsonl",
                filePath: "uploads/catalogs/8/b.jsonl",
                fileSize: 128,
                fileType: "application/json",
                uploadedAt: "2026-04-12T00:00:00Z"
              }
            ]
      )
    );
    loadAllTasksMock.mockClear();
    submitTaskMock.mockClear();
  });

  it("loads catalog assets by demand relation and clears stale file selections", async () => {
    const component = await import("@/pages/ProcessingPage.vue");
    const wrapper = mount(component.default, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          StatusPill: StatusPillStub,
          ElDialog: ElDialogStub,
          ElButton: ElButtonStub,
          ElTable: ElTableStub,
          ElTableColumn: ElTableColumnStub,
          ElSelect: ElSelectStub,
          ElOption: ElOptionStub,
          ElForm: ElFormStub,
          ElFormItem: ElFormItemStub,
          ElInput: true,
          ElInputNumber: true,
          SharedFilePreviewPanel: SharedFilePreviewPanelStub
        }
      }
    });

    const createButtons = wrapper.findAll("button").filter((item) => item.text() === "创建");
    const viewModel = wrapper.vm as unknown as {
      createForm: {
        demandId: number;
        inputAssetIds: number[];
      };
    };

    viewModel.createForm.demandId = 1;
    await nextTick();
    await flushPromises();
    expect(loadPublishedCatalogsMock).toHaveBeenCalledWith("token-123");
    expect(loadAssetsMock).toHaveBeenLastCalledWith(7, "token-123");
    expect(wrapper.text()).toContain("语料目录A");
    expect(wrapper.text()).toContain("v2026.04");
    expect(wrapper.text()).toContain("application/json");
    expect(wrapper.text()).toContain("128 B");

    viewModel.createForm.inputAssetIds = [11];
    await nextTick();
    expect(createButtons[0]?.attributes("disabled")).toBeUndefined();

    viewModel.createForm.demandId = 2;
    await nextTick();
    await flushPromises();
    expect(loadAssetsMock).toHaveBeenLastCalledWith(8, "token-123");
    expect(createButtons[0]?.attributes("disabled")).toBeDefined();
  });

  it("shows current demand and catalog summary and passes selected file into preview panel", async () => {
    const component = await import("@/pages/ProcessingPage.vue");
    const wrapper = mount(component.default, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          StatusPill: StatusPillStub,
          ElDialog: ElDialogStub,
          ElButton: ElButtonStub,
          ElTable: ElTableStub,
          ElTableColumn: ElTableColumnStub,
          ElSelect: ElSelectStub,
          ElOption: ElOptionStub,
          ElForm: ElFormStub,
          ElFormItem: ElFormItemStub,
          ElInput: true,
          ElInputNumber: true,
          SharedFilePreviewPanel: SharedFilePreviewPanelStub
        }
      }
    });

    const viewModel = wrapper.vm as unknown as {
      createForm: {
        demandId: number;
      };
    };

    viewModel.createForm.demandId = 1;
    await nextTick();
    await flushPromises();

    const previewButton = wrapper.findAll("button").find((item) => item.text() === "预览");
    expect(previewButton).toBeDefined();

    await previewButton?.trigger("click");
    await nextTick();

    expect(wrapper.text()).toContain("当前所选需求");
    expect(wrapper.text()).toContain("需求一");
    expect(wrapper.text()).toContain("目录摘要");
    expect(wrapper.text()).toContain("平台上传");
    expect(wrapper.get("[data-test='preview-panel']").text()).toContain("a.jsonl");
  });
});
