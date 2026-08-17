import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Icon, PageHead, RiskPill, DisclaimerStrip } from '../components/ui'

export default function History() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.history().then((d) => setItems(d.items)).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <PageHead
        title="Submission History"
        sub="Prototype verification sessions stored locally in SQLite. Open any row to inspect its full multi-layer analysis."
      />
      <DisclaimerStrip />

      {error && <div className="error-box"><b>Problem:</b> {error}</div>}

      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Title</th>
              <th>Date / Time</th>
              <th>Language</th>
              <th>Risk Level</th>
              <th>Status</th>
              <th>Similarity</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items === null && !error && (
              <tr><td colSpan={7} className="muted">Loading…</td></tr>
            )}
            {items?.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  No submissions yet — run a verification from the Verify Title page.
                </td>
              </tr>
            )}
            {items?.map((it) => (
              <tr key={it.id} onClick={() => navigate(`/result/${it.id}`)}>
                <td style={{ fontWeight: 600 }}>
                  {it.title}
                  {it.parent_id && (
                    <span className="faint small" style={{ marginLeft: 8 }}>↩ resubmission</span>
                  )}
                </td>
                <td className="mono faint">{it.created_at_iso}</td>
                <td className="muted">{it.language_detected || '—'}</td>
                <td><RiskPill level={it.risk_level} /></td>
                <td className="muted small">
                  {it.risk_level === 'LOW RISK' ? 'Looks clear (demo)' : it.risk_level === 'REVIEW' ? 'Manual review suggested' : 'Likely conflict (demo)'}
                </td>
                <td className="mono">{it.risk_score}<span className="faint">/100</span></td>
                <td>
                  <span className="row-flex small" style={{ color: 'var(--cyan)', gap: 6 }}>
                    <Icon name="search" size={13} /> View analysis
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
