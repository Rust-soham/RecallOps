import { ArrowUpRight, Check, Github, Menu, Radio, X } from "lucide-react"
import { motion } from "motion/react"
import { useState } from "react"
import "./landing.css"

const GITHUB_URL = "https://github.com/Rust-soham/RecallOps"

const features = [
  ["01", "Capture", "Agents record decisions, constraints, failures, and fixes through one shared MCP interface."],
  ["02", "Verify", "Review competing claims side by side, with the evidence that made each agent believe them."],
  ["03", "Improve", "Approved truth supersedes stale context and moves into Cognee's durable knowledge graph."],
  ["04", "Handoff", "Every new session starts with a focused, provenance-rich briefing—not a transcript dump."],
]

export function Landing() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="landing">
      <nav className="landing-nav">
        <a className="landing-brand" href="/">
          <span>R</span><strong>RecallOps</strong>
        </a>
        <div className={`landing-links ${menuOpen ? "open" : ""}`}>
          <a href="#how">How it works</a>
          <a href="#proof">The proof</a>
          <a href={GITHUB_URL} target="_blank" rel="noreferrer"><Github size={14} /> GitHub</a>
        </div>
        <a className="landing-cta" href={GITHUB_URL} target="_blank" rel="noreferrer">View on GitHub <ArrowUpRight size={15} /></a>
        <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">
          {menuOpen ? <X /> : <Menu />}
        </button>
      </nav>

      <header className="landing-hero">
        <div className="orbit"><i /><i /><i /></div>
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55 }}>
          <div className="landing-pill"><span /> Memory control plane for AI agents</div>
          <h1>Agents forget.<br /><em>Your project</em> can’t.</h1>
          <div className="hero-bottom">
            <p>RecallOps turns scattered agent context into reviewed project truth—shared across Codex, OpenCode, and every session after.</p>
            <div className="powered"><span /><small>Powered by<br /><b>Cognee graph memory</b></small></div>
          </div>
        </motion.div>
      </header>

      <section className="proof-section" id="proof">
        <div className="landing-wrap">
          <div className="landing-heading">
            <div><small>The proof, not the pitch</small><h2>One decision.<br /><span>Every future session.</span></h2></div>
            <code>LIVE RELAY / 01</code>
          </div>
          <div className="proof-flow">
            <Relay number="01" agent="OPENCODE" title="Learns" body="HTTP-only cookies—not localStorage JWTs." />
            <div className="flow-arrow"><small>record</small><i /><ArrowUpRight size={14} /></div>
            <Relay number="02" agent="RECALLOPS + COGNEE" title="Reviews & remembers" body="Human-approved truth with source provenance." central />
            <div className="flow-arrow"><small>handoff</small><i /><ArrowUpRight size={14} /></div>
            <Relay number="03" agent="CODEX" title="Recalls" body="A fresh session starts with the correct decision." />
          </div>
        </div>
      </section>

      <section className="how-section" id="how">
        <div className="how-intro"><small>Why RecallOps</small><h2>Memory needs a <em>review layer.</em></h2></div>
        <div className="feature-grid">
          {features.map(([n, title, body]) => <article key={n}><code>{n}</code><h3>{title}</h3><p>{body}</p></article>)}
        </div>
      </section>

      <section className="truth-section">
        <div className="truth-copy">
          <small>Trusted by design</small>
          <h2>The agent said it.<br />RecallOps proves <em>why.</em></h2>
          <ul>
            <li><Check size={14} /> Human-reviewed project truth</li>
            <li><Check size={14} /> Evidence attached to every claim</li>
            <li><Check size={14} /> Stale decisions explicitly superseded</li>
          </ul>
        </div>
        <div className="truth-card">
          <div><span><Radio size={13} /> CURRENT PROJECT TRUTH</span><code>auth.session-strategy</code></div>
          <blockquote>“Authentication will use HTTP-only cookie sessions.”</blockquote>
          <footer><span><i /> ACTIVE · APPROVED</span><small>security-review.md ↗</small></footer>
        </div>
      </section>

      <section className="final-cta">
        <h2>Switch agents.<br />Not context.</h2>
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">Explore the project <ArrowUpRight /></a>
      </section>

      <footer className="landing-footer">
        <div className="landing-brand light"><span>R</span><strong>RecallOps</strong></div>
        <p>Built for the Cognee Hackathon</p>
      </footer>
    </div>
  )
}

function Relay({ number, agent, title, body, central = false }: { number: string; agent: string; title: string; body: string; central?: boolean }) {
  return <article className={`relay-demo ${central ? "central" : ""}`}><code>{number} / {agent}</code><div><i /><h3>{title}</h3><p>{body}</p></div></article>
}
