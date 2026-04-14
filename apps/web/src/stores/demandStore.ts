import { defineStore } from "pinia";

import { approveDemand, createDemand, fetchDemands } from "@/api/demands";
import { getErrorMessage } from "@/api/http";
import type { DemandCreatePayload, DemandItem } from "@/types/demand";

interface DemandState {
  items: DemandItem[];
  loading: boolean;
  error: string | null;
}

export const useDemandStore = defineStore("demand", {
  state: (): DemandState => ({
    items: [],
    loading: false,
    error: null
  }),
  getters: {
    pendingCount: (state) => state.items.filter((item) => item.status === "pending_approval").length,
    activeCount: (state) => state.items.filter((item) => item.status !== "rejected" && item.status !== "delivered").length,
    deliveredCount: (state) => state.items.filter((item) => item.status === "delivered").length
  },
  actions: {
    async loadAll(token: string) {
      await this.load(async () => {
        this.items = await fetchDemands(token);
      });
    },
    async submit(payload: DemandCreatePayload, token: string) {
      this.error = null;
      try {
        const demand = await createDemand(payload, token);
        this.upsertItem(demand);
        return demand;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async approve(id: number, reviewNote: string, token: string) {
      this.error = null;
      try {
        const demand = await approveDemand(id, reviewNote, token);
        this.upsertItem(demand);
        return demand;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    upsertItem(next: DemandItem) {
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
