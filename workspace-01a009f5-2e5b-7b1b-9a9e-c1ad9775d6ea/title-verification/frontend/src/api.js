const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.message || `Request failed (${res.status})`)
    err.hint = data.hint
    err.payload = data
    throw err
  }
  return data
}

export const api = {
  health: () => request('/api/health'),
  config: () => request('/api/config'),
  verify: (payload) =>
    request('/api/verify', { method: 'POST', body: JSON.stringify(payload) }),
  resubmit: (payload) =>
    request('/api/resubmit', { method: 'POST', body: JSON.stringify(payload) }),
  similar: (title) => request(`/api/similar?title=${encodeURIComponent(title)}`),
  history: () => request('/api/history'),
  historyItem: (id) => request(`/api/history/${id}`),
  dataset: () => request('/api/dataset'),
}
