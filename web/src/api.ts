import type { ConflictRecord, MemoryRecord, ProjectOverview } from "./types"

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8787"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: { message?: string } }
      | null
    throw new Error(body?.detail?.message ?? `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export const api = {
  overview: (project: string) =>
    request<ProjectOverview>(`/api/projects/${project}/overview`),
  memories: (project: string) =>
    request<MemoryRecord[]>(`/api/projects/${project}/memories`),
  conflicts: (project: string) =>
    request<ConflictRecord[]>(`/api/projects/${project}/conflicts`),
  approve: (
    memoryId: string,
    supersedeMemoryId: string | null,
    reason: string,
  ) =>
    request<MemoryRecord>(`/api/memories/${memoryId}/approve`, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({
        supersede_memory_id: supersedeMemoryId,
        reason,
      }),
    }),
  reset: (project: string) =>
    request<MemoryRecord>(`/api/projects/${project}/reset`, { method: "POST" }),
  eventUrl: (project: string) =>
    `${API_BASE}/api/events/stream?project=${encodeURIComponent(project)}`,
}

