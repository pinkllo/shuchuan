import { http } from "@/api/http";
import type { TaskStatus } from "@/types/task";

export interface QuickTaskItem {
  id: number;
  demandId: number;
  catalogId: number;
  catalogName: string;
  inputAssetIds: number[];
  taskType: string;
  status: TaskStatus;
  progress: number;
  note: string | null;
  processorId: number | null;
  processorName: string | null;
  createdAt: string;
}

export interface QuickTaskCreatePayload {
  catalogId: number;
  inputAssetIds: number[];
  taskType: string;
  config: Record<string, string>;
}

interface BackendQuickTask {
  id: number;
  demand_id: number;
  catalog_id: number;
  catalog_name: string;
  input_asset_ids: number[];
  task_type: string;
  status: TaskStatus;
  progress: number;
  note: string | null;
  processor_id: number | null;
  processor_name: string | null;
  created_at: string;
}

export async function fetchQuickTasks(token: string): Promise<QuickTaskItem[]> {
  const response = await http<BackendQuickTask[]>("/api/quick-tasks", { token });
  return response.map(mapQuickTask);
}

export async function createQuickTask(
  payload: QuickTaskCreatePayload,
  token: string
): Promise<QuickTaskItem> {
  const response = await http<BackendQuickTask>("/api/quick-tasks", {
    method: "POST",
    token,
    body: {
      catalog_id: payload.catalogId,
      input_asset_ids: payload.inputAssetIds,
      task_type: payload.taskType,
      config: payload.config,
    },
  });
  return mapQuickTask(response);
}

function mapQuickTask(item: BackendQuickTask): QuickTaskItem {
  return {
    id: item.id,
    demandId: item.demand_id,
    catalogId: item.catalog_id,
    catalogName: item.catalog_name,
    inputAssetIds: item.input_asset_ids,
    taskType: item.task_type,
    status: item.status,
    progress: item.progress,
    note: item.note,
    processorId: item.processor_id,
    processorName: item.processor_name,
    createdAt: item.created_at,
  };
}
