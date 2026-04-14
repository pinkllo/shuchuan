import { http } from "@/api/http";
import type { DemandCreatePayload, DemandItem } from "@/types/demand";

interface BackendDemand {
  id: number;
  catalog_id: number;
  requester_id: number;
  provider_id: number;
  title: string;
  purpose: string;
  delivery_plan: string;
  status: DemandItem["status"];
  approval_note: string | null;
  created_at: string;
}

export async function fetchDemands(token: string): Promise<DemandItem[]> {
  const response = await http<BackendDemand[]>("/api/demands", { token });
  return response.map(mapDemand);
}

export async function createDemand(payload: DemandCreatePayload, token: string): Promise<DemandItem> {
  const response = await http<BackendDemand>("/api/demands", {
    method: "POST",
    token,
    body: {
      catalog_id: payload.catalogId,
      title: payload.title,
      purpose: payload.purpose,
      delivery_plan: payload.deliveryPlan
    }
  });

  return mapDemand(response);
}

export async function approveDemand(id: number, reviewNote: string, token: string): Promise<DemandItem> {
  const response = await http<BackendDemand>(`/api/demands/${id}/approve`, {
    method: "POST",
    token,
    body: { review_note: reviewNote }
  });

  return mapDemand(response);
}

function mapDemand(item: BackendDemand): DemandItem {
  return {
    id: item.id,
    catalogId: item.catalog_id,
    requesterId: item.requester_id,
    providerId: item.provider_id,
    title: item.title,
    purpose: item.purpose,
    deliveryPlan: item.delivery_plan,
    status: item.status,
    approvalNote: item.approval_note,
    createdAt: item.created_at
  };
}
