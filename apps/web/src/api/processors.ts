import { http } from "@/api/http";
import type { Processor } from "@/types/processor";

interface BackendProcessor {
  id: number;
  name: string;
  task_type: string;
  description: string;
  endpoint_url: string;
  status: Processor["status"];
  last_heartbeat_at: string;
  registered_at: string;
}

export async function fetchProcessors(token: string): Promise<Processor[]> {
  const response = await http<BackendProcessor[]>("/api/processors", { token });
  return response.map(mapProcessor);
}

export async function fetchOnlineProcessors(token: string): Promise<Processor[]> {
  const processors = await fetchProcessors(token);
  return processors.filter((processor) => processor.status === "online");
}

function mapProcessor(item: BackendProcessor): Processor {
  return {
    id: item.id,
    name: item.name,
    taskType: item.task_type,
    description: item.description,
    endpointUrl: item.endpoint_url,
    status: item.status,
    lastHeartbeatAt: item.last_heartbeat_at,
    registeredAt: item.registered_at,
  };
}
