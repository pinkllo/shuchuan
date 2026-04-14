import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createCatalog } from "@/api/catalogs";

const fetchMock = vi.fn<typeof fetch>();

describe("catalog api", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits catalog creation as multipart form data with repeated files", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 12,
          provider_id: 4,
          name: "课程论坛问答集",
          data_type: "text",
          granularity: "主题/帖子/回复",
          version: "v2026.04",
          fields_description: "标题、正文、回复内容",
          scale_description: "12000 条",
          upload_method: "平台上传",
          sensitivity_level: "internal",
          description: "教育问答语料",
          status: "draft",
          asset_count: 2,
          created_at: "2026-04-12T00:00:00Z"
        }),
        {
          status: 201,
          headers: { "content-type": "application/json" }
        }
      )
    );

    const fileA = new File(["alpha"], "qa-a.jsonl", { type: "application/json" });
    const fileB = new File(["beta"], "qa-b.jsonl", { type: "application/json" });

    const created = await createCatalog(
      {
        name: "课程论坛问答集",
        dataType: "text",
        granularity: "主题/帖子/回复",
        version: "v2026.04",
        fieldsDescription: "标题、正文、回复内容",
        scaleDescription: "12000 条",
        uploadMethod: "平台上传",
        sensitivityLevel: "internal",
        description: "教育问答语料",
        files: [fileA, fileB]
      },
      "token-123"
    );

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, request] = fetchMock.mock.calls[0];
    expect(request?.method).toBe("POST");
    expect(request?.headers).toBeInstanceOf(Headers);

    const headers = request?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.has("Content-Type")).toBe(false);

    const body = request?.body;
    expect(body).toBeInstanceOf(FormData);

    const formData = body as FormData;
    expect(formData.get("name")).toBe("课程论坛问答集");
    expect(formData.get("upload_method")).toBe("平台上传");
    expect(formData.getAll("files")).toEqual([fileA, fileB]);
    expect(created.assetCount).toBe(2);
  });
});
