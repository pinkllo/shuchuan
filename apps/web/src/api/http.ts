export class HttpError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

type JsonPayload = Record<string, unknown> | readonly unknown[];
type RequestBody = BodyInit | JsonPayload | null | undefined;

interface HttpOptions extends Omit<RequestInit, "body"> {
  body?: RequestBody;
  token?: string | null;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "请求失败";
}

export async function http<T>(path: string, options: HttpOptions = {}): Promise<T> {
  const { body, headers, token, ...init } = options;
  const isJsonBody = isJsonPayload(body);
  const response = await fetch(buildApiUrl(path), {
    ...init,
    body: serializeBody(body, isJsonBody),
    headers: buildHeaders(headers, token, isJsonBody)
  });

  if (!response.ok) {
    throw new HttpError(response.status, await readErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function buildHeaders(
  headers: HeadersInit | undefined,
  token: string | null | undefined,
  isJsonBody: boolean
): Headers {
  const requestHeaders = new Headers(headers);

  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  if (isJsonBody && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  return requestHeaders;
}

function isJsonPayload(value: RequestBody): value is JsonPayload {
  if (value === null || value === undefined) {
    return false;
  }

  if (value instanceof FormData || value instanceof Blob || typeof value === "string") {
    return false;
  }

  return Array.isArray(value) || Object.prototype.toString.call(value) === "[object Object]";
}

function serializeBody(body: RequestBody, isJsonBody: boolean): BodyInit | undefined {
  if (body === null || body === undefined) {
    return undefined;
  }

  if (isJsonBody) {
    return JSON.stringify(body);
  }

  return body;
}

async function readErrorMessage(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) {
    return response.statusText || "请求失败";
  }

  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    return text;
  }

  return text;
}
