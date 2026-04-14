import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const {
  createCatalogMock,
  fetchCatalogsMock,
  fetchMyCatalogsMock,
  publishCatalogMock,
  archiveCatalogMock,
  fetchCatalogAssetsMock,
  appendCatalogAssetsMock,
  deleteCatalogAssetMock
} = vi.hoisted(() => ({
  createCatalogMock: vi.fn(),
  fetchCatalogsMock: vi.fn(),
  fetchMyCatalogsMock: vi.fn(),
  publishCatalogMock: vi.fn(),
  archiveCatalogMock: vi.fn(),
  fetchCatalogAssetsMock: vi.fn(),
  appendCatalogAssetsMock: vi.fn(),
  deleteCatalogAssetMock: vi.fn()
}));

vi.mock("@/api/catalogs", () => ({
  createCatalog: createCatalogMock,
  fetchCatalogs: fetchCatalogsMock,
  fetchMyCatalogs: fetchMyCatalogsMock,
  publishCatalog: publishCatalogMock,
  archiveCatalog: archiveCatalogMock
}));

vi.mock("@/api/catalogAssets", () => ({
  fetchCatalogAssets: fetchCatalogAssetsMock,
  appendCatalogAssets: appendCatalogAssetsMock,
  deleteCatalogAsset: deleteCatalogAssetMock
}));

import { useCatalogStore } from "@/stores/catalogStore";

describe("catalogStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    createCatalogMock.mockReset();
    fetchCatalogsMock.mockReset();
    fetchMyCatalogsMock.mockReset();
    publishCatalogMock.mockReset();
    archiveCatalogMock.mockReset();
    fetchCatalogAssetsMock.mockReset();
    appendCatalogAssetsMock.mockReset();
    deleteCatalogAssetMock.mockReset();
  });

  it("loads, appends, and removes catalog assets while syncing asset counts", async () => {
    const store = useCatalogStore();
    store.items = [
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
        assetCount: 1,
        createdAt: "2026-04-12T00:00:00Z"
      }
    ];

    fetchCatalogAssetsMock.mockResolvedValue([
      {
        id: 31,
        catalogId: 9,
        uploadedBy: 2,
        fileName: "seed.jsonl",
        filePath: "uploads/catalogs/9/seed.jsonl",
        fileSize: 128,
        fileType: "application/json",
        uploadedAt: "2026-04-12T00:00:00Z"
      }
    ]);
    appendCatalogAssetsMock.mockResolvedValue([
      {
        id: 32,
        catalogId: 9,
        uploadedBy: 2,
        fileName: "append-a.jsonl",
        filePath: "uploads/catalogs/9/append-a.jsonl",
        fileSize: 256,
        fileType: "application/json",
        uploadedAt: "2026-04-12T00:10:00Z"
      },
      {
        id: 33,
        catalogId: 9,
        uploadedBy: 2,
        fileName: "append-b.jsonl",
        filePath: "uploads/catalogs/9/append-b.jsonl",
        fileSize: 512,
        fileType: "application/json",
        uploadedAt: "2026-04-12T00:11:00Z"
      }
    ]);

    await store.loadAssets(9, "token-123");

    expect(fetchCatalogAssetsMock).toHaveBeenCalledWith(9, "token-123");
    expect(store.assetsForCatalog(9)).toHaveLength(1);
    expect(store.items[0]?.assetCount).toBe(1);

    const files = [
      new File(["a"], "append-a.jsonl", { type: "application/json" }),
      new File(["b"], "append-b.jsonl", { type: "application/json" })
    ];
    await store.appendAssets(9, files, "token-123");

    expect(appendCatalogAssetsMock).toHaveBeenCalledWith(9, files, "token-123");
    expect(store.assetsForCatalog(9)).toHaveLength(3);
    expect(store.items[0]?.assetCount).toBe(3);

    await store.removeAsset(9, 32, "token-123");

    expect(deleteCatalogAssetMock).toHaveBeenCalledWith(9, 32, "token-123");
    expect(store.assetsForCatalog(9).map((item) => item.id)).toEqual([31, 33]);
    expect(store.items[0]?.assetCount).toBe(2);
  });
});
