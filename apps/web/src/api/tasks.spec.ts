import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createTask, fetchTasks } from "@/api/tasks";

const fetchMock = vi.fn<typeof fetch>();

describe("tasks api", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits multiple input asset ids when creating a task", async () => {
    fetchMock.mockResolvedValue(
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

  it("maps processor metadata from backend tasks", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: 9,
            demand_id: 3,
            input_asset_ids: [11, 12],
            created_by: 5,
            processor_id: 7,
            processor_name: "拆书服务",
            task_type: "book_split",
            status: "running",
            progress: 25,
            note: "正在拆分",
            created_at: "2026-04-12T00:00:00Z"
          }
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" }
        }
      )
    );

    const tasks = await fetchTasks("token-123");

    expect(tasks[0]?.processorId).toBe(7);
    expect(tasks[0]?.processorName).toBe("拆书服务");
  });
});
