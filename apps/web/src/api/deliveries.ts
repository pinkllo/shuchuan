import { http } from "@/api/http";
import type { DeliveryItem } from "@/types/delivery";

interface BackendDelivery {
  demand_id: number;
  demand_title: string;
  artifact_file_name: string;
  sample_count: number;
  delivered_at: string;
}

export async function fetchDeliveries(token: string): Promise<DeliveryItem[]> {
  const response = await http<BackendDelivery[]>("/api/deliveries", { token });
  return response.map((item) => ({
    demandId: item.demand_id,
    demandTitle: item.demand_title,
    artifactFileName: item.artifact_file_name,
    sampleCount: item.sample_count,
    deliveredAt: item.delivered_at
  }));
}


export async function downloadDelivery(
  demandId: number,
  fileName: string,
  token: string
): Promise<void> {
  const response = await fetch(
    `${(import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "")}/api/deliveries/${demandId}/download`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "下载失败");
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(objectUrl);
}
