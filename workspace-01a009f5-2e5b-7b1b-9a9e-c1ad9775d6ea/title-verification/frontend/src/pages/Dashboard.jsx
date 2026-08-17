import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Icon, PageHead, RiskPill, DisclaimerStrip } from '../components/ui'

const FLOW = ['INPUT', 'VALIDATE', 'COMPARE', 'RETRIEVE', 'DECIDE', 'EXPLAIN']

export default function Dashboard({ health }) {
  const navigate = useNavigate()
  const [recent, setRecent] = useState([])

  useEffect(() => {
    api.history().then((h) => setRecent(h.items.slice(0, 4))).catch(() => {})
  }, [])

  return (
    <div>
      <PageHead
        title="AI Title Verification"
        sub="Intelligent title verification using rule-based validation, string similarity, phonetic matching and multilingual semantic similarity."
      />
      <DisclaimerStrip />

      <div className="grid cols-4">
        <div className="card stat-card">
          <div className="stat-icon"><Icon name="database" /></div>
          <div className="stat-value mono">~160,000</div>
          <div className="stat-label">Real-world reference scale (PSS06 context)</div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon"><Icon name="layers" /></div>
          <div className="stat-value mono">MULTI-LAYER</div>
          <div className="stat-label">Verification — rules + string + phonetic + semantic</div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon"><Icon name="waves" /></div>
          <div className="stat-value mono">PHONETIC</div>
          <div className="stat-label">Soundex + Metaphone sound-alike detection</div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon"><Icon name="brain" /></div>
          <div className="stat-value mono">SEMANTIC</div>
          <div className="stat-label">
            {health?.semantic_engine?.fallback
              ? 'Multilingual concepts (demo engine active)'
              : 'Multilingual AI embeddings'}
          </div>
        </div>
      </div>

      <div className="grid split-wide section-gap">
        <div className="card">
          <h3>Verification Pipeline</h3>
          <p className="card-sub">
            Architecture ready to scale from the demo dataset to the ~160,000-title real-world
            reference scale: new title → preprocessing → search index → top-K candidate retrieval →
            detailed multi-layer similarity analysis.
          </p>
          <div className="flow" style={{ margin: '18px 0 6px' }}>
            {FLOW.map((f, i) => (
              <React.Fragment key={f}>
                <div className="flow-node">{f}</div>
                {i < FLOW.length - 1 && <span className="flow-arrow">→</span>}
              </React.Fragment>
            ))}
          </div>
          <div className="section-gap btn-row">
            <button className="btn btn-primary btn-lg" onClick={() => navigate('/verify')}>
              <Icon name="shield" size={17} /> VERIFY NEW TITLE
            </button>
            <Link className="btn btn-ghost" to="/how-it-works">
              <Icon name="layers" size={16} /> Architecture
            </Link>
          </div>
        </div>

        <div className="card">
          <h3>
            PROTOTYPE DATABASE{' '}
            <span className="badge prototype" style={{ marginLeft: 6 }}>Demo</span>
          </h3>
          <p className="card-sub">Representative demo dataset — not the official PRGI database.</p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <span className="mono" style={{ fontSize: 42, fontWeight: 800, color: 'var(--cyan)' }}>
              {health?.demo_titles ?? '—'}
            </span>
            <span className="muted small">demo titles indexed</span>
          </div>
          <div className="small muted" style={{ lineHeight: 1.7, marginTop: 8 }}>
            English · Hindi · Marathi · Gujarati records with exact duplicates, spelling variants,
            phonetic variants and meaning-level pairs.
          </div>
          <div className="engine-note">
            engine: {health?.semantic_engine?.label || 'loading…'}
          </div>
        </div>
      </div>

      {recent.length > 0 && (
        <div className="card section-gap">
          <div className="row-flex" style={{ justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0 }}>Recent Prototype Verifications</h3>
            <Link to="/history" className="small">
              View all →
            </Link>
          </div>
          <div className="section-gap" style={{ marginTop: 14 }}>
            {recent.map((r) => (
              <div
                key={r.id}
                className="row-flex"
                style={{
                  justifyContent: 'space-between',
                  padding: '10px 2px',
                  borderTop: '1px solid var(--border)',
                  cursor: 'pointer',
                }}
                onClick={() => navigate(`/result/${r.id}`)}
              >
                <span style={{ fontWeight: 600 }}>{r.title}</span>
                <span className="row-flex" style={{ gap: 14 }}>
                  <span className="small faint mono">{r.created_at_iso}</span>
                  <RiskPill level={r.risk_level} />
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
