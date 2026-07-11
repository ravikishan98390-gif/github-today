/**
 * ResultPanel — displays the API response.
 *
 * Variants:
 *   success       — code is valid
 *   error         — code has validation errors
 *   request-error — network / HTTP error calling the API
 */
export default function ResultPanel({ result }) {
  if (!result) return null

  // ── Network / HTTP error ──────────────────────────────────────
  if (result.kind === 'request-error') {
    return (
      <div className="result-panel request-error" role="alert">
        <div className="result-header">
          <div className="result-icon">⚠️</div>
          <span className="result-title">Request Failed</span>
        </div>
        <div className="result-body">
          <ul className="error-list">
            <li className="error-item">
              <div className="error-dot" style={{ background: 'var(--warn)' }} />
              <pre className="error-text" style={{ borderLeftColor: 'var(--warn)' }}>
                {result.message}
              </pre>
            </li>
          </ul>
        </div>
      </div>
    )
  }

  const { valid, language, source, filename, errors } = result

  // ── Valid code ────────────────────────────────────────────────
  if (valid) {
    return (
      <div className="result-panel success" role="status">
        <div className="result-header">
          <div className="result-icon">✅</div>
          <span className="result-title">Looks good — code is valid!</span>
          <div className="result-meta">
            <span className="result-badge">{language.toUpperCase()}</span>
            <span className="result-badge">{source === 'file' ? '📎 File' : '📝 Pasted'}</span>
          </div>
        </div>
        <div className="result-body">
          <p className="success-check">
            {language === 'python'
              ? 'Python syntax parsed successfully via the ast module — no errors detected.'
              : 'Java structural checks passed — class declaration, balanced braces, and parentheses all look correct.'}
          </p>
          {filename && (
            <div className="stats-row">
              <span className="stat-chip">📄 {filename}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── Invalid code (validation errors) ─────────────────────────
  return (
    <div className="result-panel error" role="alert">
      <div className="result-header">
        <div className="result-icon">❌</div>
        <span className="result-title">Validation Failed</span>
        <div className="result-meta">
          <span className="result-badge">{language.toUpperCase()}</span>
          <span className="result-badge">
            {errors.length} {errors.length === 1 ? 'error' : 'errors'}
          </span>
        </div>
      </div>
      <div className="result-body">
        <ul className="error-list" aria-label="Validation errors">
          {errors.map((err, i) => (
            <li key={i} className="error-item">
              <div className="error-dot" />
              <pre className="error-text">{err}</pre>
            </li>
          ))}
        </ul>
        {filename && (
          <div className="stats-row" style={{ marginTop: 16 }}>
            <span className="stat-chip">📄 {filename}</span>
            <span className="stat-chip">📌 {source}</span>
          </div>
        )}
      </div>
    </div>
  )
}
