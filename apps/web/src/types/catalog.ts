export type CatalogStatus = "draft" | "published" | "archived";

export interface CatalogItem {
  id: number;
  providerId: number;
  name: string;
  dataType: string;
  granularity: string;
  version: string;
  fieldsDescription: string;
  scaleDescription: string;
  sensitivityLevel: string;
  description: string;
  status: CatalogStatus;
  createdAt: string;
}

export interface CatalogCreatePayload {
  name: string;
  dataType: string;
  granularity: string;
  version: string;
  fieldsDescription: string;
  scaleDescription: string;
  sensitivityLevel: string;
  description: string;
}

export const catalogStatusLabels: Record<CatalogStatus, string> = {
  draft: "草稿",
  published: "已发布",
  archived: "已归档"
};

export const catalogStatusTones: Record<CatalogStatus, "warn" | "good" | "info"> = {
  draft: "warn",
  published: "good",
  archived: "info"
};

export const sensitivityLabels: Record<string, string> = {
  public: "公开",
  internal: "内部",
  sensitive: "敏感"
};

export function formatSensitivity(level: string): string {
  return sensitivityLabels[level] ?? level;
}
