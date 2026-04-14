import { afterEach, describe, expect, it, vi } from "vitest";

import { createTask } from "@/api/tasks";

describe("tasks api", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("submits multiple input asset ids when creating a task", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 9,
          demand_id: 3,
          input_asset_ids: [11, 12],
          created_by: 5,
          task_type: "instruction",
          status: "queued",
          progress: 0,
          note: null,
          created_at: "2026-04-12T00:00:00Z"
        }),
        {
          status: 201,
          headers: { "content-type": "application/json" }
        }
      )
    );

    vi.stubGlobal("fetch", fetchMock);

    const task = await createTask(
      {
        demandId: 3,
        inputAssetIds: [11, 12],
        taskType: "instruction",
        config: {
          model: "Qwen-2.5-72B",
          promptTemplate: "标准问答模板"
        }
      },
      "token-123"
    );

    const [, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    const payload = JSON.parse(String(request.body)) as {
      input_asset_ids: number[];
    };

    expect(payload.input_asset_ids).toEqual([11, 12]);
    expect(task.inputAssetIds).toEqual([11, 12]);
  });
});
