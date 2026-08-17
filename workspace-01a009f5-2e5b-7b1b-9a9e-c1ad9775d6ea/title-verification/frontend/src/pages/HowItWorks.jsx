import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Icon, PageHead, DisclaimerStrip } from '../components/ui'

const LAYERS = [
  {
    num: '01', name: 'Input Layer', sub: 'New title intake',
    body: 'The applicant enters the proposed title, the language (with Auto Detect) and optional submission details such as description / category.',
    tags: ['new title', 'language', 'submission details'],
  },
  {
    num: '02', name: 'Preprocessing', sub: 'Text normalisation',
    body: 'Titles are normalised before comparison: lower-casing, Unicode-aware tokenisation, special-character handling and whitespace collapsing, so visually-equivalent spellings compare fairly.',
    tags: ['text normalization', 'tokenization', 'special-character handling'],
  },
  {
    num: '03', name: 'Rule Engine', sub: 'Demo policy checks',
    body: 'Deterministic prototype checks: disallowed demo terms, common prefix/suffix variations of existing titles, periodicity-related patterns, existing-title combinations, excessive punctuation and invalid / empty titles. These are demonstration rules, not official PRGI policy.',
    tags: ['disallowed words', 'prefix/suffix rules', 'periodicity rules', 'existing-title combinations'],
  },
  {
    num: '04', name: 'Similarity Engine', sub: 'Three parallel signals',
    body: 'String layer: Levenshtein distance + Jaro-Winkler. Phonetic layer: Soundex + Metaphone detect sound-alike titles such as Phoenix / Foenix. Semantic layer: multilingual embeddings with cosine similarity (with a clearly-labelled demo concept-matching fallback) catch meaning-level matches such as Daily Evening / Pratidin Sandhya.',
    tags: ['levenshtein', 'jaro-winkler', 'soundex', 'metaphone', 'embeddings', 'cosine similarity'],
  },
  {
    num: '05', name: 'Search & Retrieval', sub: 'Top-K candidates',
    body: 'Instead of deeply comparing against every record, a cheap indexed pass retrieves the Top-K candidates from the demo database; detailed multi-signal analysis runs only on those. This is the architecture that conceptually scales to the ~160,000-title reference scale.',
    tags: ['indexed database', 'vector/search index', 'top-k candidates'],
  },
  {
    num: '06', name: 'Decision Engine', sub: 'Transparent prototype scoring',
    body: 'Each signal feeds a weighted composite: string 25% · phonetic 20% · semantic 35% · rule violations 10% · existing-title overlap 10%. Demonstration thresholds: 0–35 LOW RISK, 36–65 REVIEW, 66–100 HIGH RISK. All weights and thresholds are configurable in the backend.',
    tags: ['similarity signals', 'rule violations', 'prototype risk assessment'],
  },
  {
    num: '07', name: 'Output', sub: 'Explainable result',
    body: 'The applicant receives the risk level, per-signal scores, the closest matching titles, and a plain-language explanation of why the title was flagged — plus the Modify → Resubmit feedback loop to iterate on the title immediately.',
    tags: ['accept / reject / review', 'reasons', 'similar titles'],
  },
]

export default function HowItWorks({ health }) {
  const [cfg, setCfg] = useState(null)
  useEffect(() => { api.config().then(setCfg).catch(() => {}) }, [])

  return (
    <div>
      <PageHead
        title="How It Works"
        sub="The seven-layer verification architecture from the PSS06 problem statement, implemented as a working prototype."
      />
      <DisclaimerStrip />

      <div className="arch-stack">
        {LAYERS.map((l) => (
          <div className="layer" key={l.num}>
            <div className="lnum">{l.num}</div>
            <div className="lname">
              {l.name}
              <div className="lsub">{l.sub}</div>
            </div>
            <div className="lbody">
              {l.body}
              <div className="ltags">
                {l.tags.map((t) => <span className="ltag" key={t}>{t}</span>)}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid cols-2 section-gap">
        <div className="card">
          <h3>Prototype Scoring — Demonstration Weights</h3>
          <p className="card-sub">
            Live backend configuration. These are prototype demonstration weights only, not an
            official verification score; they are configurable via environment variables.
          </p>
          <table className="weights">
            <tbody>
              {[
                ['String similarity', 'string_similarity'],
                ['Phonetic similarity', 'phonetic_similarity'],
                ['Semantic similarity', 'semantic_similarity'],
                ['Rule violations', 'rule_violations'],
                ['Existing-title overlap', 'existing_overlap'],
              ].map(([label, key]) => (
                <tr key={key}>
                  <td>{label}</td>
                  <td className="w-bar">
                    <div className="bar" style={{ height: 7 }}>
                      <i style={{ width: `${(cfg?.weights?.[key] ?? 0.2) * 100 * 2.2}%`, maxWidth: '100%' }} />
                    </div>
                  </td>
                  <td className="w-val">{Math.round((cfg?.weights?.[key] ?? 0) * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="threshold-row">
            <span className="threshold-chip">0–{Math.round((cfg?.thresholds?.review ?? 36) - 1)} · <b style={{ color: 'var(--green)' }}>LOW RISK</b></span>
            <span className="threshold-chip">{Math.round(cfg?.thresholds?.review ?? 36)}–{Math.round((cfg?.thresholds?.high ?? 66) - 1)} · <b style={{ color: 'var(--amber)' }}>REVIEW</b></span>
            <span className="threshold-chip">{Math.round(cfg?.thresholds?.high ?? 66)}–100 · <b style={{ color: 'var(--red)' }}>HIGH RISK</b></span>
          </div>
        </div>

        <div className="card">
          <h3>Scalability Concept</h3>
          <p className="card-sub">
            The real-world PSS06 context involves ~160,000 existing titles. This prototype uses a
            representative demo dataset ({health?.demo_titles ?? '…'} titles) — the architecture, not
            fake records, demonstrates the scaling path:
          </p>
          <div className="pipeline" style={{ marginTop: 6 }}>
            {['New Title', 'Preprocessing', 'Search Index', 'Top-K Candidate Retrieval', 'Detailed Similarity Analysis'].map((s, i) => (
              <div key={s} className="pipe-step active" style={{ opacity: 0.9 }}>
                <div className="pipe-icon">{i + 1}</div>
                <span className="pipe-name">{s}</span>
              </div>
            ))}
          </div>
          <div className="engine-note">
            active semantic engine: {health?.semantic_engine?.label || '…'}
          </div>
        </div>
      </div>

      <div className="card section-gap">
        <h3>Honesty & Scope</h3>
        <ul className="small muted" style={{ lineHeight: 1.9, margin: '6px 0 0', paddingLeft: 18 }}>
          <li>Student prototype built for the SIH 2026 Internal Hackathon — <b>not</b> connected to the official PRGI database.</li>
          <li>Demo dataset and demo policy rules are representative samples, invented for demonstration.</li>
          <li>All scores are “prototype similarity indicators”; no official verification probability, accuracy or benchmark is claimed.</li>
          <li>The semantic layer uses multilingual embeddings when the model is available; otherwise it falls back to a labelled demo concept-matching engine so the prototype never breaks.</li>
          <li>An optional external AI key (e.g. for narrative explanations) is never required — core verification runs fully offline.</li>
        </ul>
        <div className="btn-row section-gap" style={{ marginTop: 16 }}>
          <Link className="btn btn-primary" to="/verify"><Icon name="shield" size={15} /> Try the live verification</Link>
        </div>
      </div>
    </div>
  )
}
