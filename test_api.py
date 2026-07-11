r"""
test_api.py - Smoke tests for POST /submit-code
Run with:  .venv\Scripts\python.exe test_api.py
"""

import json
import urllib.request
import urllib.error
import uuid
import os

BASE = "http://127.0.0.1:8000"


# Helpers
# ------------------------------------------------------------------------------

def _json_post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _multipart_post(url: str, filename: str, content: bytes) -> tuple[int, dict]:
    boundary = uuid.uuid4().hex
    ext = os.path.splitext(filename)[1]
    # Detect MIME type
    mime = "text/x-python" if ext == ".py" else "text/x-java-source" if ext == ".java" else "text/plain"

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


PASS = "[PASS]"
FAIL = "[FAIL]"

results = []

def check(name: str, status: int, body: dict, *,
          expect_status: int = 200,
          expect_valid: bool | None = None,
          expect_detail_contains: str | None = None):
    ok = True
    reasons = []

    if status != expect_status:
        ok = False
        reasons.append(f"HTTP {status} != {expect_status}")

    if expect_valid is not None:
        got = body.get("valid")
        if got != expect_valid:
            ok = False
            reasons.append(f"valid={got!r} != {expect_valid!r}")

    if expect_detail_contains:
        detail = str(body.get("detail", ""))
        errors = str(body.get("errors", ""))
        if expect_detail_contains.lower() not in (detail + errors).lower():
            ok = False
            reasons.append(f"'{expect_detail_contains}' not found in response")

    tag = PASS if ok else FAIL
    label = f"{tag}  [{name}]"
    print(label)
    if not ok or os.getenv("VERBOSE"):
        print(f"     HTTP {status} | body: {json.dumps(body, indent=4)}")
    if not ok:
        for r in reasons:
            print(f"     -> {r}")

    results.append(ok)


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

print("\n" + "=" * 60)
print("  Code Submission Module - API Smoke Tests")
print("=" * 60 + "\n")

# 1. Valid Python (JSON)
s, b = _json_post(f"{BASE}/submit-code", {"code": "def add(a, b):\n    return a + b\n", "language": "python"})
check("Valid Python via JSON", s, b, expect_valid=True)

# 2. Invalid Python — SyntaxError (JSON)
s, b = _json_post(f"{BASE}/submit-code", {"code": "def broken(\n    return 42", "language": "python"})
check("Invalid Python syntax via JSON", s, b, expect_valid=False, expect_detail_contains="SyntaxError")

# 3. Valid Java (JSON)
java_ok = "public class Hello {\n    public static void main(String[] args) {\n        System.out.println(\"hi\");\n    }\n}"
s, b = _json_post(f"{BASE}/submit-code", {"code": java_ok, "language": "java"})
check("Valid Java via JSON", s, b, expect_valid=True)

# 4. Invalid Java — unbalanced braces (JSON)
java_bad = "public class Oops {\n    public void go() {\n        // brace never closed\n}"
s, b = _json_post(f"{BASE}/submit-code", {"code": java_bad, "language": "java"})
check("Invalid Java - unbalanced braces", s, b, expect_valid=False, expect_detail_contains="brace")

# 5. Java with no class declaration (JSON)
s, b = _json_post(f"{BASE}/submit-code", {"code": 'System.out.println("no class");', "language": "java"})
check("Java - no class declaration", s, b, expect_valid=False, expect_detail_contains="class")

# 6. Missing language field → 422
s, b = _json_post(f"{BASE}/submit-code", {"code": "print(1)"})
check("Missing 'language' field", s, b, expect_status=422)

# 7. Empty code → 422
s, b = _json_post(f"{BASE}/submit-code", {"code": "   ", "language": "python"})
check("Empty code field", s, b, expect_status=422)

# 8. Unsupported language → 422
s, b = _json_post(f"{BASE}/submit-code", {"code": "x = 1", "language": "ruby"})
check("Unsupported language value", s, b, expect_status=422)

# 9. Valid .py file upload
py_valid = b"def greet(name):\n    return f'Hello, {name}'\n"
s, b = _multipart_post(f"{BASE}/submit-code", "greet.py", py_valid)
check("Valid .py file upload", s, b, expect_valid=True)

# 10. Invalid .py file upload
py_bad = b"def missing_colon\n    pass"
s, b = _multipart_post(f"{BASE}/submit-code", "bad.py", py_bad)
check("Invalid .py file upload", s, b, expect_valid=False, expect_detail_contains="SyntaxError")

# 11. Valid .java file upload
java_file = b"public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"
s, b = _multipart_post(f"{BASE}/submit-code", "HelloWorld.java", java_file)
check("Valid .java file upload", s, b, expect_valid=True)

# 12. Broken .java file upload
java_broken = b"public class Broken {\n    public void test() {\n        System.out.println(\"oops\");\n    \n}"
s, b = _multipart_post(f"{BASE}/submit-code", "Broken.java", java_broken)
check("Broken .java file upload", s, b, expect_valid=False)

# 13. Unsupported .txt file upload → 400
s, b = _multipart_post(f"{BASE}/submit-code", "notes.txt", b"some text")
check("Unsupported .txt file upload", s, b, expect_status=400, expect_detail_contains="Unsupported file type")

# 14. Public class name mismatch → invalid
wrong_name = b"public class WrongName {\n    public static void main(String[] args) {}\n}"
s, b = _multipart_post(f"{BASE}/submit-code", "HelloWorld.java", wrong_name)
check("Java public class name mismatch", s, b, expect_valid=False, expect_detail_contains="match")

# 15. Health check
req = urllib.request.Request(f"{BASE}/", method="GET")
with urllib.request.urlopen(req) as r:
    hb = json.loads(r.read())
check("Health check GET /", r.status, hb, expect_status=200)

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
passed = sum(results)
total = len(results)
print(f"\n{'=' * 60}")
print(f"  Results: {passed}/{total} passed", "[ALL PASS]" if passed == total else "[SOME FAILED]")
print(f"{'=' * 60}\n")

if passed < total:
    raise SystemExit(1)
