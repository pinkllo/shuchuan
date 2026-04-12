import { defineStore } from "pinia";

import { archiveCatalog, createCatalog, fetchCatalogs, fetchMyCatalogs, publishCatalog } from "@/api/catalogs";
import { getErrorMessage } from "@/api/http";
import type { CatalogCreatePayload, CatalogItem } from "@/types/catalog";

interface CatalogState {
  items: CatalogItem[];
  loading: boolean;
  error: string | null;
}

export const useCatalogStore = defineStore("catalog", {
  state: (): CatalogState => ({
    items: [],
    loading: false,
    error: null
  }),
  getters: {
    publishedItems: (state) => state.items.filter((item) => item.status === "published"),
    publishedCount: (state) => state.items.filter((item) => item.status === "published").length,
    totalCount: (state) => state.items.length
  },
  actions: {
    async loadPublished(token: string) {
      await this.load(async () => {
        this.items = await fetchCatalogs(token);
      });
    },
    async loadMine(token: string) {
      await this.load(async () => {
        this.items = await fetchMyCatalogs(token);
      });
    },
    async submitCatalog(payload: CatalogCreatePayload, token: string) {
      this.error = null;
      try {
        const catalog = await createCatalog(payload, token);
        this.items.unshift(catalog);
        return catalog;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async publish(id: number, token: string) {
      this.error = null;
      try {
        const published = await publishCatalog(id, token);
        this.upsertItem(published);
        return published;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async archive(id: number, token: string) {
      this.error = null;
      try {
        const archived = await archiveCatalog(id, token);
        this.upsertItem(archived);
        return archived;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    upsertItem(next: CatalogItem) {
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
