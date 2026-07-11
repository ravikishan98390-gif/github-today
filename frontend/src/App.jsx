import { useState } from 'react'
import LanguageSelector from './LanguageSelector'
import CodeEditor from './CodeEditor'
import FileUploadZone from './FileUploadZone'
import ResultPanel from './ResultPanel'

const API_URL = '/submit-code'

export default function App() {
  const [language, setLanguage] = useState('python')
  const [code, setCode]         = useState('')
  const [file, setFile]         = useState(null)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)

  // ── Derived state ──────────────────────────────────────────────
  const isFileMode   = file !== null
  const hasInput     = isFileMode || code.trim().length > 0
  const canSubmit    = hasInput && !loading

  // ── Handlers ──────────────────────────────────────────────────
  function handleCodeChange(val) {
    setCode(val)
    // Clear a previous file if the user starts typing
    if (val.length > 0 && file) { setFile(null) }
    setResult(null)
  }

  function handleFile(f) {
    setFile(f)
    setCode('')       // clear textarea when a file is picked
    setResult(null)
  }

  function handleClearFile() {
    setFile(null)
    setResult(null)
  }

  function handleLanguageChange(lang) {
    setLanguage(lang)
    setResult(null)
  }

  // ── Submit ─────────────────────────────────────────────────────
  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return

    setLoading(true)
    setResult(null)

    try {
      let response

      if (isFileMode) {
        // ── File upload path ────────────────────────────────
        const form = new FormData()
        form.append('file', file)
        response = await fetch(API_URL, { method: 'POST', body: form })
      } else {
        // ── JSON body path ──────────────────────────────────
        response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: code.trim(), language }),
        })
      }

      const data = await response.json()

      if (!response.ok) {
        // HTTP 4xx/5xx → show the FastAPI detail message
        const msg =
          typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail, null, 2)
        setResult({ kind: 'request-error', message: `HTTP ${response.status}: ${msg}` })
      } else {
        setResult(data)
      }
    } catch (err) {
      setResult({
        kind: 'request-error',
        message:
          err instanceof TypeError && err.message.includes('fetch')
            ? 'Cannot reach the API server. Make sure it is running on http://127.0.0.1:8000.'
            : String(err),
      })
    } finally {
      setLoading(false)
    }
  }

  // ── Clear all ────────────────────────────────────────────────
  function handleReset() {
    setCode('')
    setFile(null)
    setResult(null)
  }

  // ── Render ───────────────────────────────────────────────────
  return (
    <div className="app-wrapper">

      {/* Header */}
      <header className="app-header">
        <div className="app-logo">
          <div className="logo-badge">⚡</div>
          <h1 className="app-title">CodeLint</h1>
        </div>
        <p className="app-subtitle">
          Instant syntax &amp; structure validation for Python and Java
        </p>
      </header>

      {/* Main card */}
      <main>
        <div className="card">
          <form onSubmit={handleSubmit} noValidate>
            <div className="form-grid">

              {/* Language selector */}
              <LanguageSelector
                value={language}
                onChange={handleLanguageChange}
                disabled={loading || isFileMode}
              />

              {/* Code textarea */}
              <CodeEditor
                value={code}
                onChange={handleCodeChange}
                language={language}
                disabled={loading || isFileMode}
              />

              {/* Divider */}
              <div className="divider">or</div>

              {/* File upload */}
              <FileUploadZone
                file={file}
                onFile={handleFile}
                onClear={handleClearFile}
                onLanguage={setLanguage}
                disabled={loading}
              />

              {/* Submit */}
              <button
                id="submit-btn"
                type="submit"
                className="submit-btn"
                disabled={!canSubmit}
                aria-busy={loading}
              >
                <span className="submit-btn-inner">
                  {loading ? (
                    <>
                      <span className="spinner" role="status" aria-label="Validating…" />
                      Validating…
                    </>
                  ) : (
                    <>
                      <span>⚡</span>
                      {isFileMode ? `Validate ${file.name}` : 'Validate Code'}
                    </>
                  )}
                </span>
              </button>

            </div>
          </form>

          {/* Result panel */}
          <ResultPanel result={result} />

          {/* Reset link */}
          {result && !loading && (
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <button
                id="reset-btn"
                type="button"
                onClick={handleReset}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                  transition: 'color var(--transition)',
                }}
                onMouseEnter={(e) => (e.target.style.color = 'var(--text-secondary)')}
                onMouseLeave={(e) => (e.target.style.color = 'var(--text-muted)')}
              >
                Clear &amp; start over
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          Powered by{' '}
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            FastAPI
          </a>
          {' '}·{' '}
          Python validated via <code>ast</code> · Java via structural analysis
        </p>
      </footer>

    </div>
  )
}
