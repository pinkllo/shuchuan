export type DemandStatus =
  | "pending_approval"
  | "approved"
  | "rejected"
  | "data_uploaded"
  | "processing"
  | "delivered";

export interface DemandItem {
  id: number;
  catalogId: number;
  requesterId: number;
  providerId: number;
  title: string;
  purpose: string;
  deliveryPlan: string;
  status: DemandStatus;
  approvalNote: string | null;
  createdAt: string;
}

export interface DemandCreatePayload {
  catalogId: number;
  title: string;
  purpose: string;
  deliveryPlan: string;
}

export interface AssetItem {
  id: number;
  demandId: number;
  uploadedBy: number;
  fileName: string;
  filePath: string;
  fileSize: number;
  fileType: string;
  uploadedAt: string;
}

export const demandStatusLabels: Record<DemandStatus, string> = {
  pending_approval: "待审批",
  approved: "已批准",
  rejected: "已拒绝",
  data_uploaded: "数据已上传",
  processing: "处理中",
  delivered: "已交付"
};

export const demandStatusTones: Record<DemandStatus, "warn" | "info" | "danger" | "good"> = {
  pending_approval: "warn",
  approved: "info",
  rejected: "danger",
  data_uploaded: "info",
  processing: "info",
  delivered: "good"
};
