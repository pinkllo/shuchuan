import { defineComponent, h, inject, nextTick, onMounted, provide, ref } from "vue";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CatalogPage from "@/pages/CatalogPage.vue";
import { useCatalogStore } from "@/stores/catalogStore";
import { useSessionStore } from "@/stores/session";

vi.mock("element-plus", () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}));

const TABLE_KEY = Symbol("table");

const ElTable = defineComponent({
  name: "ElTable",
  props: {
    data: {
      type: Array,
      required: true
    }
  },
  setup(props, { slots }) {
    const columns = ref<
      Array<{
        label?: string;
        prop?: string;
        render: (row: Record<string, unknown>) => unknown;
      }>
    >([]);

    provide(TABLE_KEY, {
      register(column: { label?: string; prop?: string; render: (row: Record<string, unknown>) => unknown }) {
        columns.value.push(column);
      }
    });

    return () =>
      h("div", { class: "table-stub" }, [
        h("div", { style: "display:none" }, slots.default?.()),
        h(
          "div",
          { class: "table-head" },
          columns.value.map((column) => h("span", column.label ?? ""))
        ),
        ...(props.data as Record<string, unknown>[]).map((row) =>
          h(
            "div",
            { class: "table-row" },
            columns.value.map((column) => h("div", { class: "table-cell" }, column.render(row)))
          )
        )
      ]);
  }
});

const ElTableColumn = defineComponent({
  name: "ElTableColumn",
  props: {
    label: String,
    prop: String
  },
  setup(props, { slots }) {
    const table = inject<{ register: (column: { label?: string; prop?: string; render: (row: Record<string, unknown>) => unknown }) => void }>(TABLE_KEY);
    onMounted(() => {
      table?.register({
        label: props.label,
        prop: props.prop,
        render(row) {
          if (slots.default) {
            return slots.default({ row });
          }
          if (!props.prop) {
            return "";
          }
          return String(row[props.prop] ?? "");
        }
      });
    });
    return () => null;
  }
});

const ElButton = defineComponent({
  name: "ElButton",
  emits: ["click"],
  setup(_, { emit, slots }) {
    return () => h("button", { onClick: () => emit("click") }, slots.default?.());
  }
});

const ElDialog = defineComponent({
  name: "ElDialog",
  props: {
    modelValue: Boolean,
    title: {
      type: String,
      default: ""
    }
  },
  emits: ["update:modelValue"],
  setup(props, { slots }) {
    return () =>
      props.modelValue
        ? h("section", { class: "dialog-stub" }, [
            h("h4", props.title),
            slots.default?.(),
            slots.footer?.()
          ])
        : null;
  }
});

const passthrough = (name: string) =>
  defineComponent({
    name,
    props: {
      modelValue: {
        type: [String, Boolean],
        default: undefined
      }
    },
    emits: ["update:modelValue"],
    setup(props, { emit, slots, attrs }) {
      if (name === "ElInput") {
        return () =>
          h("input", {
            ...attrs,
            value: props.modelValue as string | undefined,
            onInput: (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).value)
          });
      }
      if (name === "ElCheckbox") {
        return () =>
          h("label", [
            h("input", {
              type: "checkbox",
              checked: Boolean(props.modelValue),
              onChange: (event: Event) => emit("update:modelValue", (event.target as HTMLInputElement).checked)
            }),
            slots.default?.()
          ]);
      }
      return () => h("div", slots.default?.());
    }
  });

describe("CatalogPage", () => {
  beforeEach(() => {
    const pinia = createPinia();
    setActivePinia(pinia);
  });

  it("shows asset counts and lets providers open catalog asset management", async () => {
    const catalogStore = useCatalogStore();
    const sessionStore = useSessionStore();

    sessionStore.setSession({
      accessToken: "token-123",
      user: {
        id: 2,
        username: "provider",
        displayName: "Provider",
        role: "provider"
      }
    });

    catalogStore.items = [
      {
        id: 9,
        providerId: 2,
        name: "教材问答",
        dataType: "text",
        granularity: "章节/问答",
        version: "v1",
        fieldsDescription: "章节、问题、答案",
        scaleDescription: "800 条",
        uploadMethod: "平台上传",
        sensitivityLevel: "internal",
        description: "教材问答数据",
        status: "published",
        assetCount: 3,
        createdAt: "2026-04-12T00:00:00Z"
      }
    ];

    const loadMineSpy = vi.spyOn(catalogStore, "loadMine").mockResolvedValue(undefined);
    const loadAssetsSpy = vi.spyOn(catalogStore, "loadAssets").mockResolvedValue([
      {
        id: 101,
        catalogId: 9,
        uploadedBy: 2,
        fileName: "part-01.jsonl",
        filePath: "uploads/catalogs/9/part-01.jsonl",
        fileSize: 128,
        fileType: "application/json",
        uploadedAt: "2026-04-12T00:00:00Z"
      }
    ]);

    const wrapper = mount(CatalogPage, {
      global: {
        components: {
          ElButton,
          ElCheckbox: passthrough("ElCheckbox"),
          ElDialog,
          ElForm: passthrough("ElForm"),
          ElFormItem: passthrough("ElFormItem"),
          ElInput: passthrough("ElInput"),
          ElOption: passthrough("ElOption"),
          ElSelect: passthrough("ElSelect"),
          ElTable,
          ElTableColumn,
          StatusPill: defineComponent({
            name: "StatusPill",
            props: { label: String },
            setup(props) {
              return () => h("span", props.label ?? "");
            }
          })
        },
        directives: {
          loading: {}
        }
      }
    });

    await Promise.resolve();
    await nextTick();
    await nextTick();

    expect(loadMineSpy).toHaveBeenCalledWith("token-123");
    expect(wrapper.text()).toContain("文件数");
    expect(wrapper.text()).toContain("3");

    const manageButton = wrapper
      .findAll("button")
      .find((button) => button.text().includes("管理文件"));

    expect(manageButton).toBeDefined();
    await manageButton?.trigger("click");
    await nextTick();

    expect(loadAssetsSpy).toHaveBeenCalledWith(9, "token-123");
    expect(wrapper.text()).toContain("目录文件管理");
  });
});
