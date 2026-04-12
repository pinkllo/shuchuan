import { defineStore } from "pinia";

import { createTask, createTaskArtifact, fetchTasks, updateTaskStatus } from "@/api/tasks";
import { getErrorMessage } from "@/api/http";
import type {
  TaskArtifactCreatePayload,
  TaskArtifactItem,
  TaskCreatePayload,
  TaskItem,
  TaskStatus
} from "@/types/task";

interface TaskState {
  items: TaskItem[];
  artifactsByTaskId: Record<number, TaskArtifactItem[]>;
  loading: boolean;
  error: string | null;
}

export const useTaskStore = defineStore("task", {
  state: (): TaskState => ({
    items: [],
    artifactsByTaskId: {},
    loading: false,
    error: null
  }),
  getters: {
    runningCount: (state) => state.items.filter((item) => item.status === "running").length,
    completedCount: (state) => state.items.filter((item) => item.status === "completed").length,
    totalSamples: (state) =>
      Object.values(state.artifactsByTaskId)
        .flat()
        .reduce((sum, artifact) => sum + artifact.sampleCount, 0),
    artifactsForTask: (state) => (taskId: number) => state.artifactsByTaskId[taskId] ?? []
  },
  actions: {
    async loadAll(token: string) {
      await this.load(async () => {
        this.items = await fetchTasks(token);
      });
    },
    async submit(payload: TaskCreatePayload, token: string) {
      this.error = null;
      try {
        const task = await createTask(payload, token);
        this.upsertItem(task);
        return task;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async updateStatus(id: number, status: TaskStatus, note: string, token: string) {
      this.error = null;
      try {
        const task = await updateTaskStatus(id, status, note, token);
        const current = this.items.find((item) => item.id === id);
        this.upsertItem({
          ...task,
          config: current?.config
        });
        return task;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async registerArtifact(taskId: number, payload: TaskArtifactCreatePayload, token: string) {
      this.error = null;
      try {
        const artifact = await createTaskArtifact(taskId, payload, token);
        this.artifactsByTaskId[taskId] = [...(this.artifactsByTaskId[taskId] ?? []), artifact];
        return artifact;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    upsertItem(next: TaskItem) {
      const index = this.items.findIndex((item) => item.id === next.id);
      if (index === -1) {
        this.items.unshift(next);
        return;
      }
      this.items.splice(index, 1, next);
    },
    async load(loader: () => Promise<void>) {
      this.loading = true;
      this.error = null;
      try {
        await loader();
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      } finally {
        this.loading = false;
      }
    }
  }
});
