/**
 * LanguageSelector — toggles between Python and Java.
 */
export default function LanguageSelector({ value, onChange, disabled }) {
  const options = [
    { id: 'python', label: 'Python', icon: '🐍', ext: '.py' },
    { id: 'java',   label: 'Java',   icon: '☕', ext: '.java' },
  ]

  return (
    <div>
      <span className="field-label">Language</span>
      <div className="lang-row">
        {options.map((opt) => (
          <button
            key={opt.id}
            id={`lang-btn-${opt.id}`}
            type="button"
            className={`lang-btn ${value === opt.id ? 'active' : ''}`}
            onClick={() => onChange(opt.id)}
            disabled={disabled}
            aria-pressed={value === opt.id}
          >
            <span className="lang-icon">{opt.icon}</span>
            {opt.label}
            <span style={{ fontSize: '0.72rem', opacity: 0.55, fontFamily: 'var(--font-mono)' }}>
              {opt.ext}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
