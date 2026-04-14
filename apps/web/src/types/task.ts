export type TaskStatus = "queued" | "running" | "completed" | "failed";

export interface TaskItem {
  id: number;
  demandId: number;
  inputAssetIds: number[];
  createdBy: number;
  processorId?: number | null;
  processorName?: string | null;
  taskType: string;
  status: TaskStatus;
  progress: number;
  note: string | null;
  createdAt: string;
  config?: Record<string, string>;
}

export interface TaskCreatePayload {
  demandId: number;
  inputAssetIds: number[];
  taskType: string;
  config: Record<string, string>;
}

export interface TaskArtifactCreatePayload {
  artifactType: string;
  fileName: string;
  filePath: string;
  sampleCount: number;
  note?: string;
}

export interface TaskArtifactItem {
  id: number;
  taskId: number;
  artifactType: string;
  fileName: string;
  filePath: string;
  sampleCount: number;
  note: string | null;
  createdAt: string;
}

export const taskStatusLabels: Record<TaskStatus, string> = {
  queued: "排队中",
  running: "执行中",
  completed: "已完成",
  failed: "失败"
};

export const taskStatusTones: Record<TaskStatus, "warn" | "info" | "good" | "danger"> = {
  queued: "warn",
  running: "info",
  completed: "good",
  failed: "danger"
};

export const taskTypeLabels: Record<string, string> = {
  instruction: "指令生成",
  book_split: "拆书",
  grammar_fix: "病句修改"
};

export function formatTaskType(taskType: string): string {
  return taskTypeLabels[taskType] ?? taskType;
}
