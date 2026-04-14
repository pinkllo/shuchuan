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
  upload_method: string;
  sensitivity_level: string;
  description: string;
  status: CatalogItem["status"];
  asset_count: number;
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
  const formData = new FormData();
  formData.append("name", payload.name);
  formData.append("data_type", payload.dataType);
  formData.append("granularity", payload.granularity);
  formData.append("version", payload.version);
  formData.append("fields_description", payload.fieldsDescription);
  formData.append("scale_description", payload.scaleDescription);
  formData.append("upload_method", payload.uploadMethod);
  formData.append("sensitivity_level", payload.sensitivityLevel);
  formData.append("description", payload.description);
  for (const file of payload.files) {
    formData.append("files", file);
  }

  const response = await http<BackendCatalog>("/api/catalogs", {
    method: "POST",
    token,
    body: formData
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
    uploadMethod: item.upload_method,
    sensitivityLevel: item.sensitivity_level,
    description: item.description,
    status: item.status,
    assetCount: item.asset_count,
    createdAt: item.created_at
  };
}
