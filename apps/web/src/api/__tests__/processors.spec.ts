import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchOnlineProcessors, fetchProcessors } from "@/api/processors";

const fetchMock = vi.fn<typeof fetch>();

describe("processors api", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps processor payloads into frontend fields", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: 1,
            name: "拆书服务",
            task_type: "book_split",
            description: "章节拆分",
            endpoint_url: "http://localhost:9001",
            status: "online",
            last_heartbeat_at: "2026-04-14T00:00:00Z",
            registered_at: "2026-04-14T00:00:00Z"
          }
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" }
        }
      )
    );

    const processors = await fetchProcessors("token-123");

    expect(processors).toEqual([
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

  it("filters only online processors", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            id: 1,
            name: "拆书服务",
            task_type: "book_split",
            description: "",
            endpoint_url: "http://localhost:9001",
            status: "online",
            last_heartbeat_at: "2026-04-14T00:00:00Z",
            registered_at: "2026-04-14T00:00:00Z"
          },
          {
            id: 2,
            name: "病句修复",
            task_type: "grammar_fix",
            description: "",
            endpoint_url: "http://localhost:9002",
            status: "offline",
            last_heartbeat_at: "2026-04-14T00:00:00Z",
            registered_at: "2026-04-14T00:00:00Z"
          }
        ]),
        {
          status: 200,
          headers: { "content-type": "application/json" }
        }
      )
    );

    const processors = await fetchOnlineProcessors("token-123");

    expect(processors).toHaveLength(1);
    expect(processors[0]?.taskType).toBe("book_split");
  });
});
