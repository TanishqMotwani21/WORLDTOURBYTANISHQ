import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api'
import { Icon, PageHead, RiskPill, Bar, DisclaimerStrip, levelClass } from '../components/ui'

const EXAMPLES = [
  'Indian Xpress',
  'Indian Express Daily',
  'Namascar',
  'Foenix',
  'Daily Evening',
  'Pratidin Sandhya',
  'Phoenix',
]

const LANGUAGES = ['Auto Detect', 'English', 'Hindi', 'Marathi', 'Gujarati', 'Other']

const PIPE_STEPS = [
  { name: 'Text Normalization', icon: 'type' },
  { name: 'Rule-Based Validation', icon: 'scales' },
  { name: 'String Similarity', icon: 'type' },
  { name: 'Phonetic Similarity', icon: 'waves' },
  { name: 'Semantic Similarity', icon: 'brain' },
  { name: 'Candidate Retrieval', icon: 'database' },
  { name: 'Verification Assessment', icon: 'gauge' },
]

const SIGNAL_META = [
  { key: 'string_similarity', name: 'String Similarity', icon: 'type' },
  { key: 'phonetic_similarity', name: 'Phonetic Similarity', icon: 'waves' },
  { key: 'semantic_similarity', name: 'Semantic Similarity', icon: 'brain' },
  { key: 'rule_violations', name: 'Rule Violations', icon: 'scales' },
  { key: 'existing_overlap', name: 'Existing Title Overlap', icon: 'database' },
]

function Dial({ score, level }) {
  const R = 66
  const C = 2 * Math.PI * R
  const frac = Math.max(0, Math.min(100, score)) / 100
  const color =
    level === 'LOW RISK' ? 'var(--green)' : level === 'REVIEW' ? 'var(--amber)' : 'var(--red)'
  return (
    <div className="risk-dial">
      <svg width="158" height="158">
        <circle cx="79" cy="79" r={R} fill="none" stroke="rgba(94,141,255,.14)" strokeWidth="12" />
        <circle
          cx="79" cy="79" r={R} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={C} strokeDashoffset={C * (1 - frac)}
          style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(.22,.8,.3,1)' }}
        />
      </svg>
      <div className="dial-center">
        <div>
          <div className="dial-score mono" style={{ color }}>{Math.round(score)}</div>
          <div className="dial-of">/ 100</div>
        </div>
      </div>
    </div>
  )
}

function MatchCard({ m }) {
  const [open, setOpen] = useState(false)
  const simClass = m.similarity >= 66 ? 'sim-high' : m.similarity >= 36 ? 'sim-med' : 'sim-low'
  const band = m.similarity >= 66 ? 'High' : m.similarity >= 36 ? 'Medium' : 'Low'
  return (
    <div className="card match-card" onClick={() => setOpen(!open)}>
      <div className="mc-top">
        <div>
          <span className="mc-title">{m.title}</span>{' '}
          <span className="mc-lang">{m.language}</span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className={`mc-sim ${simClass}`}>{m.similarity}%</div>
          <div className="faint" style={{ fontSize: 10.5 }}>{band}</div>
        </div>
      </div>
      <div className="mc-types">
        {(m.match_types || []).length === 0 && <span className="faint small">weak composite match</span>}
        {(m.match_types || []).map((t) => (
          <span
            key={t}
            className={`match-type ${t === 'Phonetic' ? 'phonetic' : t === 'Semantic' ? 'semantic' : ''}`}
          >
            {t}
          </span>
        ))}
      </div>
      {open && (
        <div className="mc-detail" onClick={(e) => e.stopPropagation()}>
          <div className="small muted" style={{ marginBottom: 6 }}>
            Why it matched — per-signal breakdown:
          </div>
          <div className="mini-bar">
            <div className="lbl"><span>String (Levenshtein · Jaro-Winkler)</span><span className="mono">{Math.round((m.string ?? 0) * 100)}%</span></div>
            <Bar value={(m.string ?? 0) * 100} height={6} />
          </div>
          <div className="mini-bar">
            <div className="lbl"><span>Phonetic (Soundex · Metaphone)</span><span className="mono">{Math.round((m.phonetic?.score ?? 0) * 100)}%</span></div>
            <Bar value={(m.phonetic?.score ?? 0) * 100} height={6} />
          </div>
          <div className="mini-bar">
            <div className="lbl"><span>Semantic (multilingual)</span><span className="mono">{Math.round((m.semantic?.score ?? 0) * 100)}%</span></div>
            <Bar value={(m.semantic?.score ?? 0) * 100} height={6} />
          </div>
          {m.semantic?.shared_concepts?.length > 0 && (
            <div className="small" style={{ marginTop: 6, color: '#7dd3fc' }}>
              shared meaning: {m.semantic.shared_concepts.join(', ')}
            </div>
          )}
          {m.phonetic?.best_pair && (
            <div className="small mono" style={{ marginTop: 6, color: '#d8b4fe' }}>
              “{m.phonetic.best_pair.token_a}” ↔ “{m.phonetic.best_pair.token_b}” · metaphone{' '}
              {m.phonetic.best_pair.codes.metaphone.join(' / ')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Verify() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const [phase, setPhase] = useState('form') // form | processing | result
  const [title, setTitle] = useState('')
  const [language, setLanguage] = useState('Auto Detect')
  const [description, setDescription] = useState('')
  const [parentId, setParentId] = useState(null)
  const [previousResult, setPreviousResult] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [stepState, setStepState] = useState([]) // 'wait' | 'active' | 'done'
  const [pipeDetails, setPipeDetails] = useState({})
  const timers = useRef([])

  // Load an existing result when arriving via /result/:id
  useEffect(() => {
    if (id) {
      api
        .historyItem(id)
        .then((r) => {
          setResult(r)
          setTitle(r.title)
          setLanguage(r.language === 'auto' ? 'Auto Detect' : r.language)
          setDescription(r.description || '')
          setParentId(r.id)
          setPreviousResult(r.previous_result || null)
          setPhase('result')
        })
        .catch((e) => setError(e.message))
    }
  }, [id])

  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  const startPipeline = () => {
    setStepState(PIPE_STEPS.map((_, i) => (i === 0 ? 'active' : 'wait')))
    setPipeDetails({})
    timers.current.forEach(clearTimeout)
    timers.current = []
    let acc = 420
    PIPE_STEPS.forEach((_, i) => {
      timers.current.push(
        setTimeout(() => {
          setStepState((s) => s.map((v, j) => (j === i ? 'done' : j === i + 1 ? 'active' : v)))
        }, acc)
      )
      acc += 330 + Math.random() * 240
    })
    return acc + 250
  }

  const clearPipeline = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
    setStepState([])
    setPipeDetails({})
  }

  async function runVerification({ resubmit = false } = {}) {
    setError(null)
    if (!title.trim()) {
      setError('Enter a proposed title before verification.')
      return
    }
    setPhase('processing')
    const duration = startPipeline()
    const langParam = language === 'Auto Detect' ? 'auto' : language
    try {
      const call = resubmit && parentId
        ? api.resubmit({ parent_id: parentId, title: title.trim(), language: langParam, description })
        : api.verify({ title: title.trim(), language: langParam, description, parent_id: parentId })
      const [r] = await Promise.all([
        call,
        new Promise((res) => setTimeout(res, duration)),
      ])
      // map real pipeline details from the backend
      const det = {}
      ;(r.pipeline || []).forEach((p) => { det[p.step] = p.detail })
      setPipeDetails(det)
      setStepState(PIPE_STEPS.map(() => 'done'))
      if (r.previous_result) setPreviousResult(r.previous_result)
      setResult(r)
      setParentId(r.id)
      setTimeout(() => setPhase('result'), 350)
      if (r.id) window.history.replaceState(null, '', `#/result/${r.id}`)
    } catch (e) {
      clearPipeline()
      setPhase(parentId && result ? 'result' : 'form')
      setError(e.hint ? `${e.message} ${e.hint}` : e.message)
    }
  }

  function handleModify() {
    // go back to the form with the existing title populated; keep parent link
    setPhase('form')
    setResult(null)
    clearPipeline()
    if (location.pathname.startsWith('/result/')) navigate('/verify', { replace: true })
  }

  function handleNew() {
    setTitle(''); setDescription(''); setParentId(null)
    setPreviousResult(null); setResult(null); setError(null)
    clearPipeline(); setPhase('form')
    navigate('/verify', { replace: true })
  }

  /* ============================ FORM ============================ */
  if (phase === 'form') {
    return (
      <div>
        <PageHead
          title={parentId ? 'Modify & Resubmit Title' : 'Verify a New Title'}
          sub={parentId
            ? 'Edit the title below and run the verification again — the feedback loop from the PSS06 workflow.'
            : 'Submit a proposed title through the multi-layer prototype verification pipeline.'}
        />
        <DisclaimerStrip />

        {previousResult && (
          <div className="card section-gap" style={{ marginTop: 0, marginBottom: 18, padding: '14px 20px' }}>
            <div className="row-flex small">
              <span className="faint">Previous result:</span>
              <b>{previousResult.title}</b>
              <RiskPill level={previousResult.risk_level} />
              <span className="mono muted">{previousResult.risk_score}/100</span>
            </div>
          </div>
        )}

        <div className="grid split">
          <div className="card">
            {error && <div className="error-box" style={{ marginBottom: 16 }}><b>Problem:</b> {error}</div>}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                runVerification({ resubmit: Boolean(parentId) })
              }}
            >
              <div className="field">
                <label>Title</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter proposed title"
                  autoFocus
                  maxLength={500}
                />
              </div>
              <div className="grid cols-2">
                <div className="field">
                  <label>Language</label>
                  <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    {LANGUAGES.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Description / Category (optional)</label>
                  <input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g. Evening daily, Mumbai region"
                    maxLength={500}
                  />
                </div>
              </div>
              <div className="field">
                <label>Try demonstration examples</label>
                <div className="chips">
                  {EXAMPLES.map((ex) => (
                    <button type="button" key={ex} className="chip" onClick={() => setTitle(ex)}>
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
              <div className="btn-row" style={{ marginTop: 8 }}>
                <button type="submit" className="btn btn-primary btn-lg">
                  <Icon name={parentId ? 'redo' : 'bolt'} size={17} />
                  {parentId ? 'RESUBMIT FOR VERIFICATION' : 'VERIFY TITLE'}
                </button>
                {parentId && (
                  <button type="button" className="btn btn-ghost" onClick={handleNew}>
                    Start fresh
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="card">
            <h3>What will be checked</h3>
            <p className="card-sub">Every title flows through all layers of the prototype engine:</p>
            <div className="pipeline">
              {PIPE_STEPS.map((s) => (
                <div key={s.name} className="pipe-step active" style={{ opacity: 0.85 }}>
                  <div className="pipe-icon"><Icon name={s.icon} size={13} /></div>
                  <span className="pipe-name">{s.name}</span>
                </div>
              ))}
            </div>
            <div className="engine-note">
              Result levels: LOW RISK (0–35) · REVIEW (36–65) · HIGH RISK (66–100) — composite of
              prototype similarity indicators.
            </div>
          </div>
        </div>
      </div>
    )
  }

  /* ========================= PROCESSING ========================= */
  if (phase === 'processing') {
    return (
      <div>
        <PageHead title="Running Verification Pipeline" sub={`Analysing “${title}” across the prototype layers…`} />
        <DisclaimerStrip />
        <div className="card" style={{ maxWidth: 720 }}>
          <div className="pipeline">
            {PIPE_STEPS.map((s, i) => (
              <div key={s.name} className={`pipe-step ${stepState[i] || 'wait'}`}>
                <div className="pipe-icon">
                  {stepState[i] === 'done' ? <Icon name="check" size={13} />
                    : stepState[i] === 'active' ? <span className="spinner" />
                    : <Icon name={s.icon} size={13} />}
                </div>
                <span className="pipe-name">✓ {s.name}</span>
                {pipeDetails[s.name] && <span className="pipe-detail">{pipeDetails[s.name]}</span>}
              </div>
            ))}
          </div>
          {stepState.every((s) => s === 'done') && (
            <div className="analysis-complete"><Icon name="check" size={15} /> ANALYSIS COMPLETE</div>
          )}
        </div>
      </div>
    )
  }

  /* ========================== RESULT ========================== */
  const r = result
  if (!r) return null
  const showModify = r.risk.level === 'REVIEW' || r.risk.level === 'HIGH RISK'
  const phon = r.signals.phonetic_similarity
  const sem = r.signals.semantic_similarity
  const rules = r.signals.rule_violations
  const ovl = r.signals.existing_overlap

  return (
    <div className="result-anim">
      <PageHead title="Verification Result" sub={`Prototype similarity indicators for “${r.title}” — ${r.language_detected}.`} />
      <DisclaimerStrip />

      {r.resubmission && r.previous_result && (
        <div className="resubmit-strip">
          <div className="rs-node">
            <div className="rs-lbl">Previous Result</div>
            <div className="rs-title">{r.previous_result.title}</div>
            <div style={{ marginTop: 6 }}><RiskPill level={r.previous_result.risk_level} /></div>
          </div>
          <div className="rs-arrow">→</div>
          <div className="rs-node">
            <div className="rs-lbl">Modified Title</div>
            <div className="rs-title">{r.title}</div>
            <div className="small faint" style={{ marginTop: 6 }}>edited & resubmitted</div>
          </div>
          <div className="rs-arrow">→</div>
          <div className="rs-node">
            <div className="rs-lbl">New Result</div>
            <div className="rs-title mono">{r.risk.score}/100</div>
            <div style={{ marginTop: 6 }}><RiskPill level={r.risk.level} /></div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="risk-hero">
          <Dial score={r.risk.score} level={r.risk.level} />
          <div className="risk-meta" style={{ flex: 1, minWidth: 240 }}>
            <span className={`risk-level-pill ${levelClass(r.risk.level)}`}>{r.risk.level}</span>
            <h3 style={{ marginTop: 12 }}>Overall Assessment — “{r.title}”</h3>
            <div className="risk-note">
              Composite prototype score {r.risk.score}/100, calculated from the five similarity
              indicators below using transparent demonstration weights
              (String {r.weights.string_similarity * 100}% · Phonetic {r.weights.phonetic_similarity * 100}% ·
              Semantic {r.weights.semantic_similarity * 100}% · Rules {r.weights.rule_violations * 100}% ·
              Overlap {r.weights.existing_overlap * 100}%).
              These are <b>prototype similarity indicators</b> — not an official verification score.
            </div>
            <div style={{ marginTop: 10 }}>
              {phon.score >= 50 && (
                <span className="match-banner phonetic">
                  <Icon name="waves" size={14} /> PHONETIC MATCH DETECTED
                </span>
              )}
              {sem.score >= 50 && (
                <span className="match-banner semantic">
                  <Icon name="brain" size={14} /> MEANING-LEVEL SIMILARITY
                </span>
              )}
              {rules.count > 0 && (
                <span className="match-banner" style={{ color: 'var(--amber)', background: 'rgba(251,191,36,.1)', border: '1px solid rgba(251,191,36,.35)' }}>
                  <Icon name="alert" size={14} /> DEMO RULE TRIGGERED
                </span>
              )}
              {ovl.exact_duplicate && (
                <span className="match-banner" style={{ color: 'var(--red)', background: 'rgba(251,113,133,.1)', border: '1px solid rgba(251,113,133,.4)' }}>
                  <Icon name="database" size={14} /> EXACT DUPLICATE IN DEMO DATA
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid cols-2 section-gap">
        <div className="card">
          <h3>Prototype Similarity Indicators</h3>
          <p className="card-sub">Calculated scores per signal — deterministic & transparent.</p>
          {SIGNAL_META.map((s) => {
            const sig = r.signals[s.key]
            const isRule = s.key === 'rule_violations'
            const isOvl = s.key === 'existing_overlap'
            let foot = null
            if (s.key === 'string_similarity' && sig.best_match)
              foot = `Closest: “${sig.best_match.title}”`
            if (s.key === 'phonetic_similarity' && sig.detail)
              foot = `“${sig.detail.pair[0]}” ↔ “${sig.detail.pair[1]}” vs “${sig.detail.against}” · metaphone ${sig.detail.metaphone.join('/')} · soundex ${sig.detail.soundex.join('/')}`
            else if (s.key === 'phonetic_similarity')
              foot = 'No sound-alike match in demo data'
            if (s.key === 'semantic_similarity')
              foot = sig.detail?.shared_concepts?.length
                ? `Shared meaning with “${sig.detail.against}”: ${sig.detail.shared_concepts.join(', ')}`
                : sig.best_match ? `Closest: “${sig.best_match.title}”` : 'No meaning-level match in demo data'
            if (isRule)
              foot = sig.count ? sig.violations[0].message : 'No demo policy issue detected'
            if (isOvl)
              foot = sig.exact_duplicate
                ? `Identical to existing demo title “${sig.exact_duplicate}”`
                : sig.contained_in ? `Contained in “${sig.contained_in}”` : 'None detected'
            const detected = isRule ? sig.count > 0 : isOvl ? sig.score > 0 : sig.score >= 50
            return (
              <div className="signal-row" key={s.key}>
                <div className="signal-icon"><Icon name={s.icon} /></div>
                <div className="signal-head">
                  <span>
                    <span className="name">{s.name}</span>
                    {(isRule || isOvl) && (
                      <span className={`tag-flag ${detected ? 'on' : 'off'}`}>
                        {detected ? 'Detected' : 'None'}
                      </span>
                    )}
                    {s.key === 'phonetic_similarity' && sig.score >= 50 && (
                      <span className="tag-flag phon-on">Match</span>
                    )}
                    {s.key === 'semantic_similarity' && sig.score >= 50 && (
                      <span className="tag-flag sem-on">Meaning</span>
                    )}
                    <div className="algo">{sig.algorithm}</div>
                  </span>
                  <span className="val">{sig.score}<span className="faint">/100</span></span>
                </div>
                <Bar value={sig.score} />
                <div className="signal-foot" style={{ gridColumn: 2 }}>{foot}</div>
              </div>
            )
          })}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <h3>Why was this title flagged?</h3>
            <p className="card-sub">Explainable result — generated from the actual signals above.</p>
            <ul className="explain-list">
              {(r.explanations || []).map((e, i) => (
                <li key={i} className={`explain-item ${e.type}`}>
                  <span className="ex-ico">
                    <Icon name={e.type === 'success' ? 'check' : e.type === 'danger' ? 'alert' : e.type === 'warning' ? 'alert' : 'info'} size={13} />
                  </span>
                  <span>{e.text}</span>
                </li>
              ))}
            </ul>
            <div className="engine-note">
              semantic engine: {r.engine?.semantic?.label} · analysed {r.engine?.demo_titles_indexed} demo
              titles in {r.timings?.total_ms} ms
            </div>
          </div>

          <div className="card">
            <h3>Next steps</h3>
            <p className="card-sub">
              {showModify
                ? 'This title needs attention. Modify it and resubmit to see the assessment change in real time.'
                : 'This title looks distinct within the prototype demo dataset.'}
            </p>
            <div className="btn-row">
              {showModify && (
                <button className="btn btn-primary" onClick={handleModify}>
                  <Icon name="edit" size={15} /> MODIFY TITLE
                </button>
              )}
              <button className="btn btn-ghost" onClick={handleNew}>
                <Icon name="shield" size={15} /> Verify another title
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card section-gap">
        <h3>Closest Matches in the Demo Dataset</h3>
        <p className="card-sub">
          Top-K retrieval over the prototype index · click a match to see why it matched.
          Representative demo titles — not official PRGI records.
        </p>
        {(r.matches || []).length === 0 ? (
          <div className="small muted">No comparable titles found in the demo dataset — a good sign.</div>
        ) : (
          <div className="grid cols-3">
            {r.matches.map((m, i) => <MatchCard key={i} m={m} />)}
          </div>
        )}
      </div>
    </div>
  )
}
