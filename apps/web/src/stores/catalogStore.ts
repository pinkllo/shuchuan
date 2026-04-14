import { defineStore } from "pinia";

import { appendCatalogAssets, deleteCatalogAsset, fetchCatalogAssets } from "@/api/catalogAssets";
import { archiveCatalog, createCatalog, fetchCatalogs, fetchMyCatalogs, publishCatalog } from "@/api/catalogs";
import { getErrorMessage } from "@/api/http";
import type { CatalogCreatePayload, CatalogItem } from "@/types/catalog";
import type { CatalogAssetItem } from "@/types/catalogAsset";

interface CatalogState {
  items: CatalogItem[];
  assetsByCatalogId: Record<number, CatalogAssetItem[]>;
  loading: boolean;
  error: string | null;
}

export const useCatalogStore = defineStore("catalog", {
  state: (): CatalogState => ({
    items: [],
    assetsByCatalogId: {},
    loading: false,
    error: null
  }),
  getters: {
    publishedItems: (state) => state.items.filter((item) => item.status === "published"),
    publishedCount: (state) => state.items.filter((item) => item.status === "published").length,
    totalCount: (state) => state.items.length,
    assetsForCatalog: (state) => (catalogId: number) => state.assetsByCatalogId[catalogId] ?? []
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
    async loadAssets(id: number, token: string) {
      this.error = null;
      try {
        const assets = await fetchCatalogAssets(id, token);
        this.assetsByCatalogId[id] = assets;
        this.syncAssetCount(id);
        return assets;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async appendAssets(id: number, files: File[], token: string) {
      this.error = null;
      try {
        const assets = await appendCatalogAssets(id, files, token);
        const current = this.assetsByCatalogId[id] ?? [];
        this.assetsByCatalogId[id] = [...current, ...assets];
        this.syncAssetCount(id);
        return assets;
      } catch (error) {
        this.error = getErrorMessage(error);
        throw error;
      }
    },
    async removeAsset(id: number, assetId: number, token: string) {
      this.error = null;
      try {
        await deleteCatalogAsset(id, assetId, token);
        const current = this.assetsByCatalogId[id] ?? [];
        this.assetsByCatalogId[id] = current.filter((item) => item.id !== assetId);
        this.syncAssetCount(id);
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
    syncAssetCount(id: number) {
      const catalog = this.items.find((item) => item.id === id);
      if (!catalog) {
        return;
      }
      catalog.assetCount = this.assetsByCatalogId[id]?.length ?? 0;
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
