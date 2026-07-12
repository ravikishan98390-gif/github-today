# CodeLint

A full-stack code validation tool built with **FastAPI** (backend) and **React + Vite** (frontend).

## Features

- Submit Python (`.py`) or Java (`.java`) code via:
  - **JSON body** — paste code directly with a `code` + `language` field
  - **File upload** — drag-and-drop or click-to-browse `.py` / `.java` files
- **Python** syntax validated using the built-in `ast` module (exact line/column errors)
- **Java** validated with structural checks: class declaration, balanced braces/parens, unclosed comments, public class name vs filename
- Clear JSON error responses for invalid code, unsupported file types, empty submissions
- Premium dark-mode React UI with glassmorphism design

---

## Project Structure

```
.
├── main.py                  # FastAPI entry point
├── requirements.txt         # Python dependencies
├── five_scenarios.py        # Acceptance test (5 scenarios)
├── test_api.py              # Full smoke test suite (15 cases)
│
├── routers/
│   └── submit.py            # POST /submit-code endpoint
│
├── models/
│   └── schemas.py           # Pydantic request/response schemas
│
├── validators/
│   ├── python_validator.py  # ast-based Python syntax validator
│   └── java_validator.py    # Structural Java validator
│
└── frontend/                # React + Vite UI
    ├── src/
    │   ├── App.jsx
    │   ├── LanguageSelector.jsx
    │   ├── CodeEditor.jsx
    │   ├── FileUploadZone.jsx
    │   ├── ResultPanel.jsx
    │   └── index.css
    └── vite.config.js       # Dev proxy → FastAPI on :8000
```

---

## Getting Started

### Backend

```bash
# Create and activate virtual environment (uses uv)
uv venv .venv
uv pip install -r requirements.txt --python .venv/Scripts/python.exe

# Start the API server
.venv/Scripts/uvicorn.exe main:app --reload --port 8000
```

API docs available at: **http://127.0.0.1:8000/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: **http://localhost:5173**

---

## API Reference

### `POST /submit-code`

**Option A — JSON body:**
```json
{
  "code": "def hello():\n    return 42",
  "language": "python"
}
```

**Option B — File upload (multipart/form-data):**
```
field name: file
accepted:   .py, .java
max size:   1 MB
```

**Response:**
```json
{
  "valid": true,
  "language": "python",
  "source": "body",
  "filename": null,
  "message": "Code is valid.",
  "errors": []
}
```

**Error codes:**

| Code | Meaning |
|------|---------|
| `400` | Bad request — unsupported file type, empty file, wrong Content-Type |
| `413` | File exceeds 1 MB limit |
| `422` | Schema validation failed (missing/invalid fields, empty code) |

---

## Running Tests

```bash
# Full 15-case smoke suite
.venv/Scripts/python.exe test_api.py

# Five-scenario acceptance tests
.venv/Scripts/python.exe five_scenarios.py
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, Uvicorn, Pydantic v2 |
| Validation | `ast` (Python), regex/heuristic (Java) |
| Frontend | React 18, Vite, Vanilla CSS |
| Fonts | Inter, JetBrains Mono (Google Fonts) |
