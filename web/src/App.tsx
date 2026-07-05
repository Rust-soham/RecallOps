import {
  Activity,
  ArrowRight,
  Bot,
  Braces,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  Database,
  FileText,
  Fingerprint,
  GitMerge,
  LoaderCircle,
  Radio,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { api } from "./api"
import type {
  ConflictRecord,
  MemoryRecord,
  OperationEvent,
  ProjectOverview,
} from "./types"

const PROJECT =
  new URLSearchParams(window.location.search).get("project") ?? "auth-migration"

function projectLabel(project: string): string {
  return project
    .split(/[-_]/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function shortTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value))
}

function memoryById(memories: MemoryRecord[], id: string): MemoryRecord | undefined {
  return memories.find((memory) => memory.id === id)
}

export function App() {
  const [overview, setOverview] = useState<ProjectOverview | null>(null)
  const [memories, setMemories] = useState<MemoryRecord[]>([])
  const [conflicts, setConflicts] = useState<ConflictRecord[]>([])
  const [selected, setSelected] = useState<MemoryRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [action, setAction] = useState<"approve" | "reset" | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [nextOverview, nextMemories, nextConflicts] = await Promise.all([
        api.overview(PROJECT),
        api.memories(PROJECT),
        api.conflicts(PROJECT),
      ])
      setOverview(nextOverview)
      setMemories(nextMemories)
      setConflicts(nextConflicts)
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "RecallOps is unavailable.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const source = new EventSource(api.eventUrl(PROJECT))
    source.onmessage = () => void load()
    source.onerror = () => source.close()
    return () => source.close()
  }, [load])

  const openConflict = useMemo(
    () => conflicts.find((conflict) => !conflict.resolved),
    [conflicts],
  )
  const candidate = openConflict
    ? memoryById(memories, openConflict.candidate_memory_id)
    : memories.find((memory) => memory.status === "candidate")
  const current = openConflict
    ? memoryById(memories, openConflict.current_memory_id)
    : memories.find((memory) => memory.status === "active")

  async function approve() {
    if (!candidate) return
    setAction("approve")
    try {
      const approved = await api.approve(
        candidate.id,
        current?.id ?? null,
        `Reviewed evidence establishes ${candidate.subject} as current project truth.`,
      )
      setSelected(approved)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Approval failed.")
    } finally {
      setAction(null)
    }
  }

  async function reset() {
    setAction("reset")
    try {
      await api.reset(PROJECT)
      setSelected(null)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Reset failed.")
    } finally {
      setAction(null)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <span className="brand-glyph">R</span>
          <div>
            <strong>RecallOps</strong>
            <small>Memory control plane</small>
          </div>
        </div>
        <nav>
          <a className="nav-item active" href="#overview">
            <Braces size={17} /> Overview
          </a>
          <a className="nav-item" href="#truth">
            <ShieldCheck size={17} /> Project truth
            <span>{overview?.active_memories ?? 0}</span>
          </a>
          <a className="nav-item" href="#conflicts">
            <GitMerge size={17} /> Review inbox
            <span className={overview?.conflicts ? "warning-count" : ""}>
              {overview?.conflicts ?? 0}
            </span>
          </a>
          <a className="nav-item" href="#activity">
            <Activity size={17} /> Activity
          </a>
        </nav>
        <div className="sidebar-foot">
          <div className="connection">
            <span className="pulse" />
            <div>
              <strong>
                {overview?.memory_backend === "cognee"
                  ? "Cognee connected"
                  : "Demo memory adapter"}
              </strong>
              <small>
                {overview?.memory_backend === "cognee" ? "cognee" : "deterministic"} ·
                {" "}{PROJECT}
              </small>
            </div>
          </div>
          <button className="ghost-button" onClick={() => void reset()}>
            <RefreshCcw size={14} className={action === "reset" ? "spin" : ""} />
            Reset demo
          </button>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div className="breadcrumbs">
            Projects <ChevronRight size={14} /> <strong>{projectLabel(PROJECT)}</strong>
          </div>
          <div className="live-pill">
            <Radio size={13} /> Live memory feed
          </div>
        </header>

        <div className="content">
          <section className="hero" id="overview">
            <div>
              <div className="eyebrow">
                <ShieldCheck size={14} /> Trust layer for agent memory
              </div>
              <h1>
                Your agents share memory.
                <br />
                <span>Now you can trust it.</span>
              </h1>
              <p>
                Inspect what every coding agent learned, verify the evidence, and
                push only corrected project truth into the next session.
              </p>
            </div>
            <div className="hero-state">
              <span className={overview?.conflicts ? "risk-dot" : "healthy-dot"} />
              <div>
                <small>MEMORY HEALTH</small>
                <strong>{overview?.conflicts ? "Needs review" : "Verified"}</strong>
              </div>
            </div>
          </section>

          {error && (
            <div className="error-banner">
              <CircleAlert size={17} />
              <span>{error}</span>
              <button onClick={() => void load()}>Retry</button>
            </div>
          )}

          <section className="stats-grid">
            <Metric label="Canonical memories" value={overview?.active_memories ?? 0} icon={<Database />} />
            <Metric label="Pending review" value={overview?.candidates ?? 0} icon={<Clock3 />} />
            <Metric label="Improvements" value={overview?.improvements ?? 0} icon={<Sparkles />} />
            <Metric label="Fresh recalls" value={overview?.recalls ?? 0} icon={<Fingerprint />} />
          </section>

          <section className="relay-card">
            <div className="section-heading">
              <div>
                <span className="section-kicker">AGENT RELAY</span>
                <h2>One decision. Every future session.</h2>
              </div>
              <span className="event-time">
                <span className="pulse" /> streaming
              </span>
            </div>
            <div className="relay">
              <RelayNode
                label="CODEX"
                title="Learned"
                subtitle={candidate ? "Cookie-session rule" : "Waiting for candidate"}
                icon={<Bot />}
                active={Boolean(candidate)}
              />
              <RelayLine active={Boolean(candidate)} label="record" />
              <RelayNode
                label={
                  overview?.memory_backend === "cognee"
                    ? "RECALLOPS + COGNEE"
                    : "RECALLOPS · DEMO MODE"
                }
                title={overview?.improvements ? "Verified & improved" : "Human review"}
                subtitle={overview?.conflicts ? "1 conflict detected" : "Current truth ready"}
                icon={<ShieldCheck />}
                active={Boolean(overview?.improvements)}
                central
              />
              <RelayLine active={Boolean(overview?.recalls)} label="handoff" />
              <RelayNode
                label="OPENCODE"
                title={overview?.recalls ? "Recalled" : "Fresh session"}
                subtitle={overview?.recalls ? "Correct rule received" : "No chat history"}
                icon={<Braces />}
                active={Boolean(overview?.recalls)}
              />
            </div>
          </section>

          <div className="workspace-grid">
            <section className="panel truth-panel" id="conflicts">
              <div className="section-heading compact">
                <div>
                  <span className="section-kicker">REVIEW INBOX</span>
                  <h2>{candidate ? "Resolve competing project truth" : "No pending memories"}</h2>
                </div>
                {candidate && <span className="severity">HIGH IMPACT</span>}
              </div>

              {loading ? (
                <LoadingState />
              ) : candidate ? (
                <>
                  <div className="comparison">
                    {current && (
                      <MemoryChoice
                        memory={current}
                        label="CURRENT · STALE"
                        tone="stale"
                        onInspect={() => setSelected(current)}
                      />
                    )}
                    <div className="versus">VS</div>
                    <MemoryChoice
                      memory={candidate}
                      label="PROPOSED · EVIDENCED"
                      tone="proposed"
                      onInspect={() => setSelected(candidate)}
                    />
                  </div>
                  <div className="decision-bar">
                    <div>
                      <Fingerprint size={17} />
                      <span>
                        Learned by <strong>{candidate.agent}</strong> ·{" "}
                        {candidate.evidence.length} source attached
                      </span>
                    </div>
                    <button
                      className="primary-button"
                      disabled={action === "approve"}
                      onClick={() => void approve()}
                    >
                      {action === "approve" ? (
                        <LoaderCircle size={16} className="spin" />
                      ) : (
                        <Check size={16} />
                      )}
                      Approve & supersede
                    </button>
                  </div>
                </>
              ) : (
                <EmptyReview active={current} />
              )}
            </section>

            <section className="panel activity-panel" id="activity">
              <div className="section-heading compact">
                <div>
                  <span className="section-kicker">FLIGHT RECORDER</span>
                  <h2>Memory activity</h2>
                </div>
                <Activity size={18} />
              </div>
              <div className="event-list">
                <AnimatePresence initial={false}>
                  {(overview?.events ?? []).slice(0, 6).map((event) => (
                    <EventRow event={event} key={event.id} />
                  ))}
                </AnimatePresence>
                {!overview?.events.length && <p className="muted">No activity yet.</p>}
              </div>
            </section>
          </div>
        </div>
      </main>

      <AnimatePresence>
        {selected && (
          <ProvenanceDrawer memory={selected} onClose={() => setSelected(null)} />
        )}
      </AnimatePresence>
    </div>
  )
}

function Metric({
  label,
  value,
  icon,
}: {
  label: string
  value: number
  icon: React.ReactNode
}) {
  return (
    <div className="metric">
      <div className="metric-icon">{icon}</div>
      <div>
        <strong>{String(value).padStart(2, "0")}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function RelayNode({
  label,
  title,
  subtitle,
  icon,
  active,
  central = false,
}: {
  label: string
  title: string
  subtitle: string
  icon: React.ReactNode
  active: boolean
  central?: boolean
}) {
  return (
    <div className={`relay-node ${active ? "is-active" : ""} ${central ? "central" : ""}`}>
      <div className="relay-icon">{icon}</div>
      <span>{label}</span>
      <strong>{title}</strong>
      <small>{subtitle}</small>
    </div>
  )
}

function RelayLine({ active, label }: { active: boolean; label: string }) {
  return (
    <div className={`relay-line ${active ? "is-active" : ""}`}>
      <span>{label}</span>
      <div className="line-track">
        {active && <motion.i animate={{ x: ["0%", "900%"] }} transition={{ duration: 2.4, repeat: Infinity }} />}
      </div>
      <ArrowRight size={16} />
    </div>
  )
}

function MemoryChoice({
  memory,
  label,
  tone,
  onInspect,
}: {
  memory: MemoryRecord
  label: string
  tone: "stale" | "proposed"
  onInspect: () => void
}) {
  return (
    <article className={`memory-choice ${tone}`}>
      <div className="choice-top">
        <span>{label}</span>
        {tone === "stale" ? <CircleAlert size={17} /> : <ShieldCheck size={17} />}
      </div>
      <div className="subject">{memory.subject}</div>
      <p>{memory.statement}</p>
      <button onClick={onInspect}>
        <FileText size={14} /> Inspect evidence
      </button>
    </article>
  )
}

function EmptyReview({ active }: { active?: MemoryRecord }) {
  return (
    <div className="empty-review">
      <div className="empty-icon">
        <ShieldCheck size={28} />
      </div>
      <h3>{active ? "Project truth is verified" : "Waiting for Codex"}</h3>
      <p>
        {active
          ? "No memory candidates need human review."
          : "Ask Codex to call recallops_record when it discovers the approved auth decision."}
      </p>
    </div>
  )
}

function EventRow({ event }: { event: OperationEvent }) {
  return (
    <motion.div
      className="event-row"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      <div className={`event-dot ${event.type.replace(".", "-")}`} />
      <div>
        <strong>{event.title}</strong>
        <p>{event.detail}</p>
      </div>
      <time>{shortTime(event.created_at)}</time>
    </motion.div>
  )
}

function LoadingState() {
  return (
    <div className="loading-state">
      <LoaderCircle size={22} className="spin" />
      Loading project memory…
    </div>
  )
}

function ProvenanceDrawer({
  memory,
  onClose,
}: {
  memory: MemoryRecord
  onClose: () => void
}) {
  return (
    <>
      <motion.button
        aria-label="Close provenance"
        className="drawer-scrim"
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      />
      <motion.aside
        className="drawer"
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 28, stiffness: 280 }}
      >
        <div className="drawer-head">
          <div>
            <span className="section-kicker">PROVENANCE</span>
            <h2>Why does RecallOps believe this?</h2>
          </div>
          <button onClick={onClose}>×</button>
        </div>
        <div className="verified-banner">
          <ShieldCheck size={18} />
          <div>
            <strong>{memory.status === "active" ? "Canonical memory" : "Candidate memory"}</strong>
            <span>{Math.round(memory.confidence * 100)}% capture confidence</span>
          </div>
        </div>
        <dl className="metadata">
          <div><dt>Agent</dt><dd>{memory.agent}</dd></div>
          <div><dt>Session</dt><dd>{memory.session_id}</dd></div>
          <div><dt>Dataset scope</dt><dd>{memory.status === "active" ? "current" : "working"}</dd></div>
          <div><dt>Memory ID</dt><dd>{memory.id}</dd></div>
          <div><dt>Cognee entry</dt><dd>{memory.cognee_entry_id ?? "pending"}</dd></div>
        </dl>
        <div className="drawer-section">
          <span className="section-kicker">CLAIM</span>
          <p className="drawer-claim">{memory.statement}</p>
        </div>
        <div className="drawer-section">
          <span className="section-kicker">SOURCE REFERENCES</span>
          {memory.evidence.map((reference) => (
            <div className="reference-card" key={reference.uri}>
              <FileText size={18} />
              <div>
                <strong>{reference.label}</strong>
                <code>{reference.uri}</code>
                {reference.excerpt && <p>“{reference.excerpt}”</p>}
              </div>
            </div>
          ))}
        </div>
      </motion.aside>
    </>
  )
}
