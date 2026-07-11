/**
 * CodeEditor — monospace textarea with live character count.
 */
export default function CodeEditor({ value, onChange, language, disabled }) {
  const placeholders = {
    python: '# Paste your Python code here…\ndef greet(name):\n    return f"Hello, {name}!"',
    java:   '// Paste your Java code here…\npublic class Hello {\n    public static void main(String[] args) {\n        System.out.println("Hello!");\n    }\n}',
  }

  return (
    <div>
      <span className="field-label">Code</span>
      <div className="code-textarea-wrapper">
        <textarea
          id="code-input"
          className="code-textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholders[language] ?? '// Paste your code here…'}
          disabled={disabled}
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          rows={12}
          aria-label="Code input"
        />
        {value.length > 0 && (
          <span className="char-count">{value.length.toLocaleString()} chars</span>
        )}
      </div>
    </div>
  )
}
