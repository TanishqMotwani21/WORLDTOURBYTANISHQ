import React, { useEffect, useState } from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { api } from './api'
import Dashboard from './pages/Dashboard'
import Verify from './pages/Verify'
import SimilarTitles from './pages/SimilarTitles'
import History from './pages/History'
import HowItWorks from './pages/HowItWorks'
import { Icon } from './components/ui'

export default function App() {
  const [health, setHealth] = useState(null)
  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: 'error' }))
  }, [])

  const nav = [
    { to: '/dashboard', label: 'Dashboard', icon: 'grid' },
    { to: '/verify', label: 'Verify Title', icon: 'shield' },
    { to: '/similar', label: 'Similar Titles', icon: 'search' },
    { to: '/history', label: 'Submission History', icon: 'clock' },
    { to: '/how-it-works', label: 'How It Works', icon: 'layers' },
  ]

  return (
    <>
      <div className="app-bg" />
      <div className="layout">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-mark">
              <Icon name="shield" size={22} />
            </div>
            <div>
              <h1>AI TITLE VERIFICATION</h1>
              <div className="sub">CODECRAFTERS · PSS06</div>
            </div>
          </div>
          <div className="badges">
            <span className="badge prototype">Prototype</span>
            <span className="badge ghost">SIH 2026 · Internal</span>
          </div>
          <div className="nav-section">Navigation</div>
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon name={n.icon} size={17} />
              {n.label}
            </NavLink>
          ))}
          <div className="sidebar-foot">
            {health?.status === 'ok' ? (
              <>
                <span className="signal-dot" style={{ background: 'var(--green)', marginRight: 7 }} />
                API online · {health.demo_titles} demo titles
                <br />
                <span className="faint">
                  {health.semantic_engine?.fallback ? 'Demo semantic matching' : 'ST embeddings'}
                </span>
              </>
            ) : (
              <>
                <span className="signal-dot" style={{ background: 'var(--red)', marginRight: 7 }} />
                API {health ? 'error' : 'connecting…'}
              </>
            )}
            <br />
            <br />
            Thadomal Shahani Engineering College
            <br />
            18–19 August 2026
          </div>
        </aside>
        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard health={health} />} />
            <Route path="/verify" element={<Verify />} />
            <Route path="/result/:id" element={<Verify />} />
            <Route path="/similar" element={<SimilarTitles />} />
            <Route path="/history" element={<History />} />
            <Route path="/how-it-works" element={<HowItWorks health={health} />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          <div className="footer-note">
            <b>Prototype for Internal Hackathon Demonstration.</b> Uses a representative demo dataset
            and prototype scoring logic. Not connected to the official PRGI database. No official
            verification probability or accuracy is claimed. Team CODECRAFTERS · Thadomal Shahani
            Engineering College (TSEC) · Smart India Hackathon 2026 — Internal Hackathon · 18–19 August 2026.
          </div>
        </main>
      </div>
    </>
  )
}
