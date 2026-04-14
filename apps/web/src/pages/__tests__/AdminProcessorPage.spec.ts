import { defineComponent } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchProcessorsMock = vi.fn();

vi.mock("element-plus", () => ({
  ElMessage: {
    error: vi.fn()
  }
}));

vi.mock("@/api/http", () => ({
  getErrorMessage: (error: unknown) => String(error)
}));

vi.mock("@/api/processors", () => ({
  fetchProcessors: (...args: unknown[]) => fetchProcessorsMock(...args)
}));

vi.mock("@/stores/session", () => ({
  useSessionStore: () => ({
    accessToken: "token-123"
  })
}));

const StatusPillStub = defineComponent({
  name: "StatusPillStub",
  template: "<span><slot /></span>"
});

const ElButtonStub = defineComponent({
  name: "ElButtonStub",
  emits: ["click"],
  template: "<button @click=\"$emit('click')\"><slot /></button>"
});

const ElTableStub = defineComponent({
  name: "ElTableStub",
  template: "<div><slot /></div>"
});

const ElTableColumnStub = defineComponent({
  name: "ElTableColumnStub",
  props: {
    prop: {
      type: String,
      default: ""
    }
  },
  template: "<div><slot :row=\"{ status: 'online' }\" />{{ prop }}</div>"
});

describe("AdminProcessorPage", () => {
  beforeEach(() => {
    fetchProcessorsMock.mockReset();
    fetchProcessorsMock.mockResolvedValue([
      {
        id: 1,
        name: "拆书服务",
        taskType: "book_split",
        description: "章节拆分",
        endpointUrl: "http://localhost:9001",
        status: "online",
        lastHeartbeatAt: "2026-04-14T00:00:00Z",
        registeredAt: "2026-04-14T00:00:00Z"
      }
    ]);
  });

  it("loads processors on mount and shows processor management content", async () => {
    const component = await import("@/pages/AdminProcessorPage.vue");
    const wrapper = mount(component.default, {
      global: {
        directives: {
          loading: {}
        },
        stubs: {
          StatusPill: StatusPillStub,
          ElButton: ElButtonStub,
          ElTable: ElTableStub,
          ElTableColumn: ElTableColumnStub
        }
      }
    });

    await flushPromises();

    expect(fetchProcessorsMock).toHaveBeenCalledWith("token-123");
    expect(wrapper.text()).toContain("处理器管理");
    expect(wrapper.text()).toContain("taskType");
  });
});
