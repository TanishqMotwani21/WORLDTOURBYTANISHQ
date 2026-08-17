import React from 'react'

/* Inline SVG icon set (no external assets, works fully offline) */
const PATHS = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  shield: 'M12 2l8 3.5v5.2c0 5-3.4 9.4-8 10.8-4.6-1.4-8-5.8-8-10.8V5.5L12 2z',
  search: 'M10.5 3a7.5 7.5 0 105.6 12.5L21 20.4l1.4-1.4-4.9-4.9A7.5 7.5 0 0010.5 3zm0 2a5.5 5.5 0 110 11 5.5 5.5 0 010-11z',
  clock: 'M12 2a10 10 0 110 20 10 10 0 010-20zm0 2a8 8 0 100 16 8 8 0 000-16zm1 3v5.4l4 2.4-1 1.7-5-3V7h2z',
  layers: 'M12 2l10 5-10 5L2 7l10-5zm0 9.8l7.4-3.7L22 9.5 12 14.5 2 9.5l2.6-1.4L12 11.8zm0 4.3l7.4-3.7 2.6 1.4-10 5-10-5 2.6-1.4 7.4 3.7z',
  type: 'M4 4h16v3H4zM11 4h2v13h-2z',
  scales: 'M12 3v18M5 6l-3 7h6L5 6zm14 0l-3 7h6l-3-7zM5 6h14M8 21h8',
  waves: 'M2 12c2.5 0 2.5-3 5-3s2.5 3 5 3 2.5-3 5-3 2.5 3 5 3M2 18c2.5 0 2.5-3 5-3s2.5 3 5 3 2.5-3 5-3 2.5 3 5 3M2 6c2.5 0 2.5-3 5-3s2.5 3 5 3 2.5-3 5-3 2.5 3 5 3',
  brain: 'M9 3a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 003 3c.8 0 1.5-.3 2-.8V6.8c-.5-.5-1.2-.8-2-.8zm6 0c-.8 0-1.5.3-2 .8v11.4c.5.5 1.2.8 2 .8a3 3 0 003-3 3 3 0 002-5 3 3 0 00-2-5 3 3 0 00-3-3z',
  database: 'M12 2C7.6 2 4 3.8 4 6v12c0 2.2 3.6 4 8 4s8-1.8 8-4V6c0-2.2-3.6-4-8-4zm0 2c3.9 0 6 1.5 6 2s-2.1 2-6 2-6-1.5-6-2 2.1-2 6-2zm6 7.5c0 .5-2.1 2-6 2s-6-1.5-6-2V8.6c1.4 1 3.9 1.4 6 1.4s4.6-.5 6-1.4v2.9zm0 6c0 .5-2.1 2-6 2s-6-1.5-6-2v-2.9c1.4 1 3.9 1.4 6 1.4s4.6-.5 6-1.4v2.9z',
  check: 'M9.5 16.2L5.3 12l-1.4 1.4 5.6 5.6 12-12-1.4-1.4-10.6 10.6z',
  alert: 'M12 2L1 21h22L12 2zm0 4l7.5 13h-15L12 6zm-1 4v5h2v-5h-2zm0 6v2h2v-2h-2z',
  info: 'M12 2a10 10 0 110 20 10 10 0 010-20zm0 2a8 8 0 100 16 8 8 0 000-16zm-1 4h2v2h-2V8zm0 4h2v5h-2v-5z',
  edit: 'M4 20h4l10.5-10.5-4-4L4 16v4zm14.9-13.6a1 1 0 000-1.4l-2.9-2.9a1 1 0 00-1.4 0l-1.8 1.8 4 4 2.1-1.5z',
  redo: 'M12 5V2L7 6l5 4V7a5 5 0 11-5 5H5a7 7 0 107-7z',
  arrow: 'M13 5l7 7-7 7-1.4-1.4L16.2 13H4v-2h12.2l-4.6-4.6L13 5z',
  bolt: 'M13 2L4 14h6l-1 8 9-12h-6l1-8z',
  globe: 'M12 2a10 10 0 110 20 10 10 0 010-20zm0 2c-4.4 0-8 3.6-8 8a7.96 7.96 0 002.6 5.9C7.5 14.5 9.6 13 12 13s4.5 1.5 5.4 4.9A7.96 7.96 0 0020 12c0-4.4-3.6-8-8-8zm0 3a2.5 2.5 0 110 5 2.5 2.5 0 010-5z',
  list: 'M4 6h16v2H4zM4 11h16v2H4zM4 16h10v2H4z',
  gauge: 'M12 4a9 9 0 019 9c0 1.9-.6 3.6-1.6 5H4.6A9 9 0 0112 4zm0 2.4A6.6 6.6 0 005.7 16h12.6c.2-.6.4-1.2.4-2 0-3.6-3-6.6-6.7-6.6zm0 3.6l2.8 4.3a3 3 0 11-4.2-1.2L12 10z',
}

export function Icon({ name, size = 18 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d={PATHS[name] || PATHS.info} />
    </svg>
  )
}

export function levelClass(level) {
  if (level === 'LOW RISK') return 'low'
  if (level === 'REVIEW') return 'review'
  return 'high'
}

export function RiskPill({ level }) {
  return (
    <span className={`pill ${levelClass(level)}`}>
      <span
        className="signal-dot"
        style={{
          background:
            level === 'LOW RISK' ? 'var(--green)' : level === 'REVIEW' ? 'var(--amber)' : 'var(--red)',
          marginRight: 6,
        }}
      />
      {level}
    </span>
  )
}

export function Bar({ value, tone, height }) {
  const t = tone || (value >= 66 ? 'danger' : value >= 36 ? 'warn' : '')
  return (
    <div className="bar" style={height ? { height } : undefined}>
      <i className={t} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  )
}

export function PageHead({ title, sub }) {
  return (
    <div className="page-head">
      <h2>{title}</h2>
      {sub ? <p>{sub}</p> : null}
    </div>
  )
}

export function DisclaimerStrip() {
  return (
    <div className="disclaimer-strip">
      <b>Prototype for Internal Hackathon Demonstration.</b> Uses a representative demo dataset and
      prototype scoring logic. <b>Not connected to the official PRGI database.</b>
    </div>
  )
}
