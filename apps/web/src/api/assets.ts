import { http } from "@/api/http";
import type { AssetItem } from "@/types/demand";

interface BackendAsset {
  id: number;
  demand_id: number;
  uploaded_by: number;
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
}

export async function uploadDemandFiles(
  demandId: number,
  files: File[],
  token: string
): Promise<AssetItem[]> {
  const uploads: AssetItem[] = [];

  for (const file of files) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await http<BackendAsset>(`/api/demands/${demandId}/assets`, {
      method: "POST",
      token,
      body: formData
    });
    uploads.push(mapAsset(response));
  }

  return uploads;
}


export async function fetchDemandAssets(demandId: number, token: string): Promise<AssetItem[]> {
  const response = await http<BackendAsset[]>(`/api/demands/${demandId}/assets`, { token });
  return response.map(mapAsset);
}

function mapAsset(item: BackendAsset): AssetItem {
  return {
    id: item.id,
    demandId: item.demand_id,
    uploadedBy: item.uploaded_by,
    fileName: item.file_name,
    filePath: item.file_path,
    fileSize: item.file_size,
    fileType: item.file_type,
    uploadedAt: item.uploaded_at
  };
}
