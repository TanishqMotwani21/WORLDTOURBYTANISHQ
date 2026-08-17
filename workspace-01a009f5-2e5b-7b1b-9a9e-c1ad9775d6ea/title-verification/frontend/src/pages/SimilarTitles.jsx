import React, { useState } from 'react'
import { api } from '../api'
import { Icon, PageHead, Bar, DisclaimerStrip } from '../components/ui'

const QUICK = ['Indian Express', 'Pratidin Sandhya', 'Phoenix', 'Daily Star', 'Namaskar', 'Sandhya Times']

export default function SimilarTitles() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [openIdx, setOpenIdx] = useState(null)

  async function search(q) {
    const t = (q ?? query).trim()
    if (!t) return
    setLoading(true); setError(null); setOpenIdx(null)
    try {
      const d = await api.similar(t)
      setData(d)
      setQuery(t)
    } catch (e) {
      setError(e.hint ? `${e.message} ${e.hint}` : e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHead
        title="Similar Titles"
        sub="Explore the closest matches in the prototype demo dataset for any phrase — string, phonetic and semantic proximity combined."
      />
      <DisclaimerStrip />

      <div className="card">
        <form
          className="row-flex"
          onSubmit={(e) => { e.preventDefault(); search() }}
        >
          <input
            style={{
              flex: 1, minWidth: 220, padding: '13px 16px', fontSize: 15, fontFamily: 'inherit',
              background: 'rgba(6,11,28,.7)', color: 'var(--text)',
              border: '1px solid var(--border-strong)', borderRadius: 12, outline: 'none',
            }}
            placeholder="Type a title to look up similar demo records…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary" disabled={loading || !query.trim()}>
            <Icon name="search" size={15} /> {loading ? 'Searching…' : 'Find similar'}
          </button>
        </form>
        <div className="chips" style={{ marginTop: 14 }}>
          <span className="chips-label">Quick:</span>
          {QUICK.map((q) => (
            <button key={q} className="chip" onClick={() => search(q)}>{q}</button>
          ))}
        </div>
      </div>

      {error && <div className="error-box section-gap"><b>Problem:</b> {error}</div>}

      {data && (
        <div className="section-gap">
          <div className="small muted" style={{ margin: '0 2px 12px' }}>
            {data.count} comparable title(s) for <b style={{ color: 'var(--text)' }}>“{data.query}”</b> — {data.note}
          </div>
          <div className="grid cols-2">
            {data.results.map((m, i) => {
              const simClass = m.similarity >= 66 ? 'sim-high' : m.similarity >= 36 ? 'sim-med' : 'sim-low'
              const band = m.similarity >= 66 ? 'High' : m.similarity >= 36 ? 'Medium' : 'Low'
              const open = openIdx === i
              return (
                <div key={i} className="card match-card" onClick={() => setOpenIdx(open ? null : i)}>
                  <div className="mc-top">
                    <div>
                      <span className="mc-title">{m.title}</span>{' '}
                      <span className="mc-lang">{m.language}</span>
                      {m.category && <div className="faint" style={{ fontSize: 11, marginTop: 3 }}>{m.category}</div>}
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div className={`mc-sim ${simClass}`}>{m.similarity}%</div>
                      <div className="faint" style={{ fontSize: 10.5 }}>{band}</div>
                    </div>
                  </div>
                  <div className="mc-types">
                    {(m.match_types || []).map((t) => (
                      <span key={t} className={`match-type ${t === 'Phonetic' ? 'phonetic' : t === 'Semantic' ? 'semantic' : ''}`}>{t}</span>
                    ))}
                    {(m.match_types || []).length === 0 && <span className="faint small">string proximity only</span>}
                  </div>
                  {open && (
                    <div className="mc-detail" onClick={(e) => e.stopPropagation()}>
                      <div className="small muted" style={{ marginBottom: 6 }}>Why it matched:</div>
                      <div className="mini-bar">
                        <div className="lbl"><span>String similarity</span><span className="mono">{m.string}%</span></div>
                        <Bar value={m.string} height={6} />
                      </div>
                      <div className="mini-bar">
                        <div className="lbl"><span>Phonetic similarity</span><span className="mono">{m.phonetic}%</span></div>
                        <Bar value={m.phonetic} height={6} />
                      </div>
                      <div className="mini-bar">
                        <div className="lbl"><span>Semantic similarity</span><span className="mono">{m.semantic}%</span></div>
                        <Bar value={m.semantic} height={6} />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          {data.count === 0 && (
            <div className="card small muted">No comparable demo titles above the retrieval threshold.</div>
          )}
        </div>
      )}
    </div>
  )
}
