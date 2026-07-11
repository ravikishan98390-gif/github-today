r"""
five_scenarios.py
=================
Explicitly tests the five required scenarios:

  1. Valid Python file       (.py, correct syntax)
  2. Valid Java file         (.java, correct structure)
  3. Broken / invalid file   (.py with a syntax error)
  4. Empty submission        (JSON body with blank code)
  5. Unsupported file type   (.txt upload)

Run with:
  .venv\Scripts\python.exe five_scenarios.py
"""

import json
import sys
import uuid
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

# ─── helpers ──────────────────────────────────────────────────────────────────

def post_json(payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}/submit-code", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def post_file(filename: str, content: bytes) -> tuple[int, dict]:
    boundary = uuid.uuid4().hex
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    mime_map = {".py": "text/x-python", ".java": "text/x-java-source"}
    mime = mime_map.get(ext, "text/plain")

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE}/submit-code", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


PASS = "[PASS]"
FAIL = "[FAIL]"
passed_count = 0
failed_count = 0


def report(label: str, ok: bool, http: int, body: dict, notes: str = ""):
    global passed_count, failed_count
    tag = PASS if ok else FAIL
    if ok:
        passed_count += 1
    else:
        failed_count += 1
    print(f"\n  {tag}  {label}")
    print(f"         HTTP {http}")
    if notes:
        print(f"         {notes}")
    if not ok:
        print(f"         RESPONSE: {json.dumps(body, indent=9)}")


# ─── scenario 1: valid Python file ────────────────────────────────────────────

print("\n" + "=" * 66)
print("  CodeLint — Five Scenario Acceptance Tests")
print("=" * 66)

print("\n--- Scenario 1: Valid Python file ---")
py_valid = b"""\
def fibonacci(n: int) -> list[int]:
    \"\"\"Return the first n Fibonacci numbers.\"\"\"
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a)
        a, b = b, a + b
    return result

if __name__ == "__main__":
    print(fibonacci(10))
"""
http, body = post_file("fibonacci.py", py_valid)
ok = http == 200 and body.get("valid") is True
report(
    "Valid Python file (fibonacci.py)",
    ok, http, body,
    f"valid={body.get('valid')!r}  language={body.get('language')!r}  source={body.get('source')!r}"
)

# ─── scenario 2: valid Java file ──────────────────────────────────────────────

print("\n--- Scenario 2: Valid Java file ---")
java_valid = b"""\
import java.util.ArrayList;
import java.util.List;

public class Fibonacci {
    public static List<Integer> generate(int n) {
        List<Integer> result = new ArrayList<>();
        int a = 0, b = 1;
        for (int i = 0; i < n; i++) {
            result.add(a);
            int tmp = a + b;
            a = b;
            b = tmp;
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(generate(10));
    }
}
"""
http, body = post_file("Fibonacci.java", java_valid)
ok = http == 200 and body.get("valid") is True
report(
    "Valid Java file (Fibonacci.java)",
    ok, http, body,
    f"valid={body.get('valid')!r}  language={body.get('language')!r}  source={body.get('source')!r}"
)

# ─── scenario 3: broken / syntactically invalid file ──────────────────────────

print("\n--- Scenario 3: Broken / syntactically invalid file ---")
py_broken = b"""\
def greet(name
    print(f"Hello {name}")   # missing closing paren + colon on def line

class Broken
    pass                     # missing colon after class name
"""
http, body = post_json({"code": py_broken.decode(), "language": "python"})
errors = body.get("errors", [])
ok = http == 200 and body.get("valid") is False and len(errors) > 0
report(
    "Broken Python code (missing parens/colons)",
    ok, http, body,
    f"valid={body.get('valid')!r}  errors={errors}"
)

# ─── scenario 4: empty submission ─────────────────────────────────────────────

print("\n--- Scenario 4: Empty submission ---")

# 4a — whitespace-only string (Pydantic validator should reject it)
http_a, body_a = post_json({"code": "   \n\t  ", "language": "python"})
ok_a = http_a == 422

# 4b — empty string
http_b, body_b = post_json({"code": "", "language": "java"})
ok_b = http_b == 422

ok = ok_a and ok_b
report(
    "Empty submission rejected with 422",
    ok, max(http_a, http_b), {"whitespace_only": body_a, "empty_string": body_b},
    f"whitespace-only HTTP={http_a} (expect 422)  empty-string HTTP={http_b} (expect 422)"
)

# ─── scenario 5: unsupported file type ────────────────────────────────────────

print("\n--- Scenario 5: Unsupported file type (.txt) ---")
txt_content = b"This is a plain text file - not code."
http, body = post_file("notes.txt", txt_content)
detail = str(body.get("detail", ""))
ok = http == 400 and "unsupported" in detail.lower()
report(
    "Unsupported .txt file rejected with 400",
    ok, http, body,
    f"HTTP={http} (expect 400)  detail={detail!r}"
)

# ─── summary ──────────────────────────────────────────────────────────────────

total = passed_count + failed_count
print("\n" + "=" * 66)
print(f"  Results: {passed_count}/{total} scenarios passed")
print("=" * 66 + "\n")

if failed_count > 0:
    sys.exit(1)
