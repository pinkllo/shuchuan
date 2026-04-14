import { http } from "@/api/http";
import type {
  LoginPayload,
  RegistrationPayload,
  SessionPayload,
  SessionUser
} from "@/types/auth";

interface BackendUserRead {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: SessionUser["role"];
  status: NonNullable<SessionUser["status"]>;
}

interface BackendTokenResponse {
  access_token: string;
  token_type: string;
  user: BackendUserRead;
}

export async function login(payload: LoginPayload): Promise<SessionPayload> {
  const response = await http<BackendTokenResponse>("/api/auth/login", {
    method: "POST",
    body: payload
  });

  return {
    accessToken: response.access_token,
    tokenType: response.token_type,
    user: mapUserRead(response.user)
  };
}

export async function submitRegistration(payload: RegistrationPayload): Promise<{ id: number }> {
  return http<{ id: number }>("/api/auth/register", {
    method: "POST",
    body: {
      username: payload.username,
      display_name: payload.displayName,
      password: payload.password,
      email: payload.email,
      requested_role: payload.requestedRole,
      application_note: payload.applicationNote
    }
  });
}

export async function fetchCurrentUser(token: string): Promise<SessionUser> {
  const response = await http<BackendUserRead>("/api/auth/me", { token });
  return mapUserRead(response);
}

export function mapUserRead(user: BackendUserRead): SessionUser {
  return {
    id: user.id,
    username: user.username,
    displayName: user.display_name,
    email: user.email,
    role: user.role,
    status: user.status
  };
}
