import { describe, expect, it } from "vitest";

import type { CatalogItem } from "@/types/catalog";
import type { CatalogAssetItem } from "@/types/catalogAsset";
import type { DemandItem } from "@/types/demand";
import {
  buildCatalogAssetOptionLabel,
  buildCatalogOptionLabel,
  buildDemandOptionLabel,
  findCatalogById
} from "@/utils/catalogPresentation";

const sampleCatalog: CatalogItem = {
  id: 7,
  providerId: 3,
  name: "科研摘要",
  dataType: "text",
  granularity: "项目/摘要",
  version: "v1",
  fieldsDescription: "项目名、摘要",
  scaleDescription: "3200 条",
  uploadMethod: "平台上传",
  sensitivityLevel: "internal",
  description: "科研摘要数据",
  status: "published",
  assetCount: 3,
  createdAt: "2026-04-12T00:00:00Z"
};

const sampleDemand: DemandItem = {
  id: 9,
  catalogId: 7,
  requesterId: 4,
  providerId: 3,
  title: "问答清洗",
  purpose: "生成训练样本",
  deliveryPlan: "2026-05-31",
  status: "data_uploaded",
  approvalNote: "通过",
  createdAt: "2026-04-12T00:00:00Z"
};

const sampleAsset: CatalogAssetItem = {
  id: 21,
  catalogId: 7,
  uploadedBy: 3,
  fileName: "part-01.jsonl",
  filePath: "uploads/catalogs/7/part-01.jsonl",
  fileSize: 2048,
  fileType: "application/json",
  uploadedAt: "2026-04-12T00:00:00Z"
};

describe("catalogPresentation", () => {
  it("builds a dataset option label with version and catalog context", () => {
    const label = buildCatalogOptionLabel(sampleCatalog);

    expect(label).toContain("科研摘要");
    expect(label).toContain("v1");
    expect(label).toContain("text");
    expect(label).toContain("项目/摘要");
  });

  it("finds the selected catalog by id", () => {
    expect(findCatalogById([sampleCatalog], 7)).toEqual(sampleCatalog);
    expect(findCatalogById([sampleCatalog], 8)).toBeNull();
  });

  it("builds demand and asset labels with clearer context", () => {
    expect(buildDemandOptionLabel(sampleDemand, sampleCatalog)).toContain("科研摘要 v1");
    expect(buildCatalogAssetOptionLabel(sampleAsset)).toContain("2.0 KB");
  });
});
