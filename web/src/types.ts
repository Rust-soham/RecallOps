export type AgentName = "codex" | "opencode" | "demo"
export type MemoryStatus = "candidate" | "active" | "superseded" | "rejected" | "forgotten"
export type MemoryKind = "decision" | "constraint" | "failure" | "fix" | "assumption" | "question"

export type EvidenceReference = {
  label: string
  uri: string
  excerpt: string
}

export type MemoryRecord = {
  id: string
  project: string
  agent: AgentName
  session_id: string
  kind: MemoryKind
  subject: string
  statement: string
  evidence: EvidenceReference[]
  confidence: number
  status: MemoryStatus
  cognee_entry_id: string | null
  supersedes_id: string | null
  created_at: string
  updated_at: string
}

export type ConflictRecord = {
  id: string
  project: string
  subject: string
  current_memory_id: string
  candidate_memory_id: string
  resolved: boolean
  created_at: string
}

export type OperationEvent = {
  id: string
  project: string
  type: string
  title: string
  detail: string
  actor: AgentName | null
  memory_id: string | null
  status: "queued" | "running" | "succeeded" | "failed"
  created_at: string
}

export type ProjectOverview = {
  project: string
  memory_backend: "demo" | "cognee"
  candidates: number
  active_memories: number
  conflicts: number
  improvements: number
  recalls: number
  events: OperationEvent[]
}
