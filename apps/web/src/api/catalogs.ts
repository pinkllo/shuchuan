import { http } from "@/api/http";
import type { CatalogCreatePayload, CatalogItem } from "@/types/catalog";

interface BackendCatalog {
  id: number;
  provider_id: number;
  name: string;
  data_type: string;
  granularity: string;
  version: string;
  fields_description: string;
  scale_description: string;
  sensitivity_level: string;
  description: string;
  status: CatalogItem["status"];
  created_at: string;
}

export async function fetchCatalogs(token: string): Promise<CatalogItem[]> {
  const response = await http<BackendCatalog[]>("/api/catalogs", { token });
  return response.map(mapCatalog);
}

export async function fetchMyCatalogs(token: string): Promise<CatalogItem[]> {
  const response = await http<BackendCatalog[]>("/api/catalogs/mine", { token });
  return response.map(mapCatalog);
}

export async function createCatalog(payload: CatalogCreatePayload, token: string): Promise<CatalogItem> {
  const response = await http<BackendCatalog>("/api/catalogs", {
    method: "POST",
    token,
    body: {
      name: payload.name,
      data_type: payload.dataType,
      granularity: payload.granularity,
      version: payload.version,
      fields_description: payload.fieldsDescription,
      scale_description: payload.scaleDescription,
      sensitivity_level: payload.sensitivityLevel,
      description: payload.description
    }
  });

  return mapCatalog(response);
}

export async function publishCatalog(id: number, token: string): Promise<CatalogItem> {
  const response = await http<BackendCatalog>(`/api/catalogs/${id}/publish`, {
    method: "POST",
    token
  });

  return mapCatalog(response);
}

export async function archiveCatalog(id: number, token: string): Promise<CatalogItem> {
  const response = await http<BackendCatalog>(`/api/catalogs/${id}/archive`, {
    method: "POST",
    token
  });

  return mapCatalog(response);
}

function mapCatalog(item: BackendCatalog): CatalogItem {
  return {
    id: item.id,
    providerId: item.provider_id,
    name: item.name,
    dataType: item.data_type,
    granularity: item.granularity,
    version: item.version,
    fieldsDescription: item.fields_description,
    scaleDescription: item.scale_description,
    sensitivityLevel: item.sensitivity_level,
    description: item.description,
    status: item.status,
    createdAt: item.created_at
  };
}
