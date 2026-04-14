export type UserRole = "admin" | "provider" | "aggregator" | "consumer";
export type UserStatus = "active" | "disabled";
export type RegistrationStatus = "pending_review" | "approved" | "rejected";

export interface SessionUser {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
  email?: string;
  status?: UserStatus;
}

export interface SessionSnapshot {
  accessToken: string | null;
  user: SessionUser | null;
}

export interface SessionPayload {
  accessToken: string;
  tokenType?: string;
  user: SessionUser;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegistrationPayload {
  username: string;
  displayName: string;
  password: string;
  email: string;
  requestedRole: Exclude<UserRole, "admin">;
  applicationNote: string;
}

export interface RegistrationApplication {
  id: number;
  username: string;
  displayName: string;
  email: string;
  requestedRole: UserRole;
  applicationNote: string;
  status: RegistrationStatus;
  reviewNote: string | null;
  reviewedBy: number | null;
  reviewedAt: string | null;
  createdAt: string;
}

export interface RegistrationReviewPayload {
  role: UserRole;
  reviewNote: string;
}

export interface ReviewActionResponse {
  status: string;
}

export interface AdminUser {
  id: number;
  username: string;
  displayName: string;
  email: string;
  role: UserRole;
  status: UserStatus;
}

export interface AuditLogItem {
  id: number;
  actorId: number | null;
  action: string;
  targetType: string;
  targetId: number | null;
  detail: string | null;
  createdAt: string;
}

export const roleLabels: Record<UserRole, string> = {
  admin: "管理员",
  provider: "数据提供者",
  aggregator: "数据汇聚者",
  consumer: "数据使用者"
};
