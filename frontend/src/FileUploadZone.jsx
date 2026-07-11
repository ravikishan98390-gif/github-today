import { useRef, useState } from 'react'

/**
 * FileUploadZone — drag-and-drop + click-to-browse for .py/.java files.
 * Props:
 *   file        – currently selected File object (or null)
 *   onFile      – (File) => void  called when a file is chosen
 *   onClear     – ()    => void  called when the user removes the file
 *   onLanguage  – (str) => void  called with auto-detected language
 *   disabled    – boolean
 */
export default function FileUploadZone({ file, onFile, onClear, onLanguage, disabled }) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const ACCEPTED = { '.py': 'python', '.java': 'java' }

  function handleFile(f) {
    if (!f) return
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    const lang = ACCEPTED[ext]
    if (!lang) {
      alert(`Unsupported file type "${ext}".\nOnly .py and .java files are accepted.`)
      return
    }
    onFile(f)
    onLanguage(lang)
  }

  function handleChange(e) {
    handleFile(e.target.files[0])
    // reset so the same file can be re-selected after clearing
    e.target.value = ''
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    handleFile(e.dataTransfer.files[0])
  }

  function handleDragOver(e) {
    e.preventDefault()
    if (!disabled) setDragOver(true)
  }

  function handleDragLeave() { setDragOver(false) }

  const zoneClass = [
    'upload-zone',
    dragOver  ? 'drag-over' : '',
    file      ? 'has-file'  : '',
  ].filter(Boolean).join(' ')

  return (
    <div>
      <span className="field-label">Or upload a file</span>
      <div
        id="file-upload-zone"
        className={zoneClass}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="File upload zone — drag and drop or click to browse"
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click() }}
      >
        <input
          ref={inputRef}
          id="file-input"
          type="file"
          accept=".py,.java"
          onChange={handleChange}
          disabled={disabled}
          aria-hidden="true"
          tabIndex={-1}
        />

        {file ? (
          <>
            <span className="upload-icon">📄</span>
            <p className="upload-title">File ready</p>
            <div className="file-pill">
              <span className="file-pill-name">{file.name}</span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                {(file.size / 1024).toFixed(1)} KB
              </span>
              <button
                type="button"
                className="file-pill-remove"
                onClick={(e) => { e.stopPropagation(); onClear() }}
                aria-label="Remove file"
                title="Remove file"
              >
                ✕
              </button>
            </div>
          </>
        ) : (
          <>
            <span className="upload-icon">{dragOver ? '📂' : '📁'}</span>
            <p className="upload-title">
              {dragOver ? 'Drop it!' : 'Drag & drop or click to browse'}
            </p>
            <p className="upload-sub">Supports .py and .java · max 1 MB</p>
          </>
        )}
      </div>
    </div>
  )
}
