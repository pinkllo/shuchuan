import { defineStore } from "pinia";

import { fetchDemandAssets, uploadDemandFiles } from "@/api/assets";
import { approveDemand, createDemand, fetchDemands } from "@/api/demands";
import { getErrorMessage } from "@/api/http";
import type { AssetItem, DemandCreatePayload, DemandItem } from "@/types/demand";

interface DemandState {
  items: DemandItem[];
  assetsByDemandId: Record<number, AssetItem[]>;
  loading: boolean;
  error: string | null;
}

export const useDemandStore = defineStore("demand", {
  state: (): DemandState => ({
    items: [],
    assetsByDemandId: {},
    loading: false,
    error: null
  }),
  getters: {
    pendingCount: (state) => state.items.filter((item) => item.status === "pending_approval").length,
    activeCount: (state) => state.items.filter((item) => item.status !== "rejected" && item.status !== "delivered").length,
    deliveredCount: (state) => state.items.filter((item) => item.status === "delivered").length,
    assetsForDemand: (state) => (demandId: number) => state.assetsByDemandId[demandId] ?? []
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
    async upload(id: number, files: File[], token: string) {
      this.error = null;
      try {
        const assets = await uploadDemandFiles(id, files, token);
        this.assetsByDemandId[id] = assets;
        const demand = this.items.find((item) => item.id === id);
        if (demand) {
          demand.status = "data_uploaded";
        }
        return assets;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async loadAssets(id: number, token: string) {
      this.error = null;
      try {
        const assets = await fetchDemandAssets(id, token);
        this.assetsByDemandId[id] = assets;
        return assets;
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
