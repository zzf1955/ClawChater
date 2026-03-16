import type { ScreenshotItem, SummaryItem } from "./types";

function normalizeApiBase(rawValue: string | undefined): string {
  if (!rawValue) {
    return "";
  }
  return rawValue.trim().replace(/\/+$/, "");
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function buildUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export interface TimeRangeQuery {
  startTime: string;
  endTime: string;
}

function toIsoString(value: string): string | null {
  if (!value) {
    return null;
  }
  const normalized = value.length === 16 ? `${value}:00` : value;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toISOString();
}

function appendTimeRangeParams(params: URLSearchParams, query: TimeRangeQuery): void {
  const startTime = toIsoString(query.startTime);
  const endTime = toIsoString(query.endTime);
  if (startTime) {
    params.set("start_time", startTime);
  }
  if (endTime) {
    params.set("end_time", endTime);
  }
}

export async function listScreenshots(query: TimeRangeQuery & { limit: number }): Promise<ScreenshotItem[]> {
  const params = new URLSearchParams();
  appendTimeRangeParams(params, query);
  params.set("limit", String(query.limit));
  return requestJson<ScreenshotItem[]>(`/api/screenshots?${params.toString()}`);
}

export async function getScreenshot(id: number): Promise<ScreenshotItem> {
  return requestJson<ScreenshotItem>(`/api/screenshots/${id}`);
}

export function getScreenshotImageUrl(id: number): string {
  return buildUrl(`/api/screenshots/${id}/image`);
}

export async function listSummaries(query: TimeRangeQuery): Promise<SummaryItem[]> {
  const params = new URLSearchParams();
  appendTimeRangeParams(params, query);
  return requestJson<SummaryItem[]>(`/api/summaries?${params.toString()}`);
}

export async function getConfig(): Promise<Record<string, string>> {
  return requestJson<Record<string, string>>("/api/config");
}

export async function updateConfig(payload: Record<string, string>): Promise<Record<string, string>> {
  return requestJson<Record<string, string>>("/api/config", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface SyncResult {
  deleted: number;
  imported: number;
  total_db: number;
  total_files: number;
}

export async function syncDatabase(): Promise<SyncResult> {
  return requestJson<SyncResult>("/api/sync", { method: "POST" });
}

export { ApiError };
