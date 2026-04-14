import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useDemandStore } from "@/stores/demandStore";

describe("demand store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("upserts a demand in place without duplicating the list", () => {
    const store = useDemandStore();
    store.items = [
      {
        id: 5,
        catalogId: 7,
        requesterId: 3,
        providerId: 2,
        title: "科研摘要清洗需求",
        purpose: "训练数据准备",
        deliveryPlan: "2026-05-31",
        status: "pending_approval",
        approvalNote: null,
        createdAt: "2026-04-12T00:00:00Z"
      }
    ];

    store.upsertItem({
      id: 5,
      catalogId: 7,
      requesterId: 3,
      providerId: 2,
      title: "科研摘要清洗需求",
      purpose: "训练数据准备",
      deliveryPlan: "2026-05-31",
      status: "data_uploaded",
      approvalNote: "通过",
      createdAt: "2026-04-12T00:00:00Z"
    });

    expect(store.items).toHaveLength(1);
    expect(store.items[0]?.status).toBe("data_uploaded");
    expect(store.items[0]?.approvalNote).toBe("通过");
  });
});
