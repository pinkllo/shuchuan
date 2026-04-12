import { http } from "@/api/http";
import type {
  TaskArtifactCreatePayload,
  TaskArtifactItem,
  TaskCreatePayload,
  TaskItem,
  TaskStatus
} from "@/types/task";

interface BackendTask {
  id: number;
  demand_id: number;
  input_asset_id: number;
  created_by: number;
  task_type: string;
  status: TaskStatus;
  progress: number;
  note: string | null;
  created_at: string;
}

interface BackendTaskArtifact {
  id: number;
  task_id: number;
  artifact_type: string;
  file_name: string;
  file_path: string;
  sample_count: number;
  note: string | null;
  created_at: string;
}

export async function fetchTasks(token: string): Promise<TaskItem[]> {
  const response = await http<BackendTask[]>("/api/tasks", { token });
  return response.map(mapTask);
}

export async function createTask(payload: TaskCreatePayload, token: string): Promise<TaskItem> {
  const response = await http<BackendTask>("/api/tasks", {
    method: "POST",
    token,
    body: {
      demand_id: payload.demandId,
      input_asset_id: payload.inputAssetId,
      task_type: payload.taskType,
      config: payload.config
    }
  });

  return {
    ...mapTask(response),
    config: payload.config
  };
}

export async function updateTaskStatus(
  id: number,
  status: TaskStatus,
  note: string,
  token: string
): Promise<TaskItem> {
  const response = await http<BackendTask>(`/api/tasks/${id}/status`, {
    method: "POST",
    token,
    body: { status, note }
  });

  return mapTask(response);
}

export async function createTaskArtifact(
  taskId: number,
  payload: TaskArtifactCreatePayload,
  token: string
): Promise<TaskArtifactItem> {
  const response = await http<BackendTaskArtifact>(`/api/tasks/${taskId}/artifacts`, {
    method: "POST",
    token,
    body: {
      artifact_type: payload.artifactType,
      file_name: payload.fileName,
      file_path: payload.filePath,
      sample_count: payload.sampleCount,
      note: payload.note ?? null
    }
  });

  return mapArtifact(response);
}

function mapTask(item: BackendTask): TaskItem {
  return {
    id: item.id,
    demandId: item.demand_id,
    inputAssetId: item.input_asset_id,
    createdBy: item.created_by,
    taskType: item.task_type,
    status: item.status,
    progress: item.progress,
    note: item.note,
    createdAt: item.created_at
  };
}

function mapArtifact(item: BackendTaskArtifact): TaskArtifactItem {
  return {
    id: item.id,
    taskId: item.task_id,
    artifactType: item.artifact_type,
    fileName: item.file_name,
    filePath: item.file_path,
    sampleCount: item.sample_count,
    note: item.note,
    createdAt: item.created_at
  };
}
