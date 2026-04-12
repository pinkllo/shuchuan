import { mapUserRead } from "@/api/auth";
import { http } from "@/api/http";
import type {
  AdminUser,
  AuditLogItem,
  RegistrationApplication,
  RegistrationReviewPayload,
  ReviewActionResponse
} from "@/types/auth";

interface BackendRegistrationApplication {
  id: number;
  username: string;
  display_name: string;
  email: string;
  requested_role: RegistrationApplication["requestedRole"];
  application_note: string;
  status: RegistrationApplication["status"];
  review_note: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  created_at: string;
}

interface BackendAuditLogItem {
  id: number;
  actor_id: number | null;
  action: string;
  target_type: string;
  target_id: number | null;
  detail: string | null;
  created_at: string;
}

interface BackendAdminUser {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: AdminUser["role"];
  status: AdminUser["status"];
}

export async function fetchPendingRegistrations(token: string): Promise<RegistrationApplication[]> {
  const response = await http<BackendRegistrationApplication[]>("/api/admin/registrations", { token });
  return response.map(mapRegistrationApplication);
}

export async function approveRegistration(
  applicationId: number,
  payload: RegistrationReviewPayload,
  token: string
): Promise<ReviewActionResponse> {
  return http<ReviewActionResponse>(`/api/admin/registrations/${applicationId}/approve`, {
    method: "POST",
    token,
    body: {
      role: payload.role,
      review_note: payload.reviewNote
    }
  });
}

export async function rejectRegistration(
  applicationId: number,
  payload: RegistrationReviewPayload,
  token: string
): Promise<ReviewActionResponse> {
  return http<ReviewActionResponse>(`/api/admin/registrations/${applicationId}/reject`, {
    method: "POST",
    token,
    body: {
      role: payload.role,
      review_note: payload.reviewNote
    }
  });
}

export async function fetchAdminUsers(token: string): Promise<AdminUser[]> {
  const response = await http<BackendAdminUser[]>("/api/admin/users", { token });
  return response.map((item) => mapUserRead(item));
}


export async function disableUser(userId: number, token: string): Promise<AdminUser> {
  const response = await http<BackendAdminUser>(`/api/admin/users/${userId}/disable`, {
    method: "POST",
    token
  });
  return mapUserRead(response);
}


export async function enableUser(userId: number, token: string): Promise<AdminUser> {
  const response = await http<BackendAdminUser>(`/api/admin/users/${userId}/enable`, {
    method: "POST",
    token
  });
  return mapUserRead(response);
}

export async function fetchAuditLogs(token: string): Promise<AuditLogItem[]> {
  const response = await http<BackendAuditLogItem[]>("/api/admin/logs", { token });
  return response.map((item) => ({
    id: item.id,
    actorId: item.actor_id,
    action: item.action,
    targetType: item.target_type,
    targetId: item.target_id,
    detail: item.detail,
    createdAt: item.created_at
  }));
}

function mapRegistrationApplication(item: BackendRegistrationApplication): RegistrationApplication {
  return {
    id: item.id,
    username: item.username,
    displayName: item.display_name,
    email: item.email,
    requestedRole: item.requested_role,
    applicationNote: item.application_note,
    status: item.status,
    reviewNote: item.review_note,
    reviewedBy: item.reviewed_by,
    reviewedAt: item.reviewed_at,
    createdAt: item.created_at
  };
}
