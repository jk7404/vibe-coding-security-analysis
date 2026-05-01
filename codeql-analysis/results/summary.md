# CodeQL Security Analysis — Member 3 Results

**Tool**: CodeQL 2.24.0  
**Query pack**: `codeql/python-queries@1.8.1`  
**Suites run**:
- CWE-22 only: `Security/CWE-022/PathInjection.ql`
- Full suite: `python-security-and-quality.qls`

**Date**: 2026-05-01

---

## CWE-22 Path Traversal Findings (Primary Metric)

| Method | Model | CWE-22 Findings | Source | Sink |
|--------|-------|:--------------:|--------|------|
| Method 1: Unconstrained Vibe Coding | Sonnet | **0** | — | — |
| Method 2: Zero-Shot CoT | Sonnet | **0** | — | — |
| Method 3: Plan-and-Solve | Sonnet | **0** | — | — |
| Method 3: Plan-and-Solve | Haiku | **4** | `routes/upload.py:56` (`filename` URL param) | `routes/upload.py:65,68,73` (`file_path` used in path ops) |
| Method 4: TDD | Sonnet | **0** | — | — |
| Method 4: TDD | Haiku | **0** | — | — |

---

## All Security Findings (`error` severity only)

| Method | Model | CWE-22 | Debug Mode | Info Disclosure | Total |
|--------|-------|:------:|:----------:|:---------------:|:-----:|
| Method 1: Vibe Coding | Sonnet | 0 | 1 | 0 | **1** |
| Method 2: CoT | Sonnet | 0 | 1 | 0 | **1** |
| Method 3: Plan-and-Solve | Sonnet | 0 | 0 | 1 | **1** |
| Method 3: Plan-and-Solve | Haiku | **4** | 0 | 1 | **5** |
| Method 4: TDD | Sonnet | 0 | 1 | 0 | **1** |
| Method 4: TDD | Haiku | 0 | 1 | 1 | **2** |

---

## Detailed Findings per Method

### Method 1 — Unconstrained Vibe Coding (Sonnet)
- **CWE-22**: Not detected. `secure_filename()` applied to user-supplied filename before path join.
- **Debug mode** (`app.run(debug=True)` at `app.py:39`): Werkzeug interactive debugger exposed in production-equivalent run.

### Method 2 — Zero-Shot CoT (Sonnet)
- **CWE-22**: Not detected. Extension whitelist + `secure_filename()` applied.
- **Debug mode** (`app.py:48`): Same issue as Method 1.

### Method 3 — Plan-and-Solve (Sonnet)
- **CWE-22**: Not detected. Upload assigns a random UUID filename; no user input reaches the file path.
- **Info disclosure** (`app.py:126-127`): Exception `exc` string flows into HTTP response, leaking stack trace details to callers.

### Method 3 — Plan-and-Solve (Haiku) ⚠️ HIGHEST RISK
- **CWE-22 × 4** in `routes/upload.py` — `serve_avatar` GET endpoint:
  - Source: `filename` URL path parameter at `upload.py:56`
  - Sinks: `file_path.exists()` (line 65), `file_path.is_file()` (line 65), `file_path.resolve()` (line 68), `send_file(file_path, ...)` (line 73)
  - Root cause: Despite a regex guard (`FILENAME_REGEX`) at line 60, CodeQL's taint analysis does not recognize the regex as a trusted sanitizer — user-supplied `filename` flows directly into `Path(...) / filename` without explicit normalization (e.g. `os.path.basename`).
  - **Note**: The upload endpoint itself is safe (UUID filenames). The vulnerability is introduced in the separately implemented serving endpoint — a consequence of the more complex multi-file architecture.
- **Info disclosure** (`routes/upload.py:49`): `str(e)` from exception exposed in JSON response.
- **Code quality** (recommendations): 3 unused imports, 1 unused local variable.

### Method 4 — TDD (Sonnet)
- **CWE-22**: Not detected. `secure_filename()` applied; tests explicitly cover path traversal attack case.
- **Debug mode** (`app.py:41`): Same as Method 1/2.

### Method 4 — TDD (Haiku)
- **CWE-22**: Not detected. `secure_filename()` applied + null/dot-prefix check.
- **Info disclosure** (`app.py:47`): `str(e)` from file save exception exposed in HTTP response body.
- **Debug mode** (`app.py:51`): `app.run(debug=True)`.

---

## Key Findings / Interpretation

1. **CWE-22 was only triggered in Method 3 Haiku (Plan-and-Solve).** Counterintuitively, the most architecturally complex output introduced the most path traversal surface — not the unconstrained vibe-coded output.

2. **`secure_filename()` is a recognized CodeQL sanitizer.** Methods 1, 2, 4 (both models) all use `werkzeug.utils.secure_filename`, which CodeQL's taint model treats as a trusted sink-side sanitizer, suppressing CWE-22 alerts.

3. **Method 3 Haiku split upload and serve into separate endpoints**, adding a URL-parameter-driven serving route that introduces a new taint path. The regex-based guard (`FILENAME_REGEX`) is not recognized by CodeQL as sufficient — a known limitation of regex-based sanitization vs. explicit `basename`/`realpath` normalization.

4. **`debug=True` is ubiquitous** across Methods 1, 2, 4. All three methods leave the Werkzeug interactive debugger enabled — a high-severity issue in any internet-exposed deployment.

5. **Information disclosure via `str(e)`** appears in all Haiku outputs (Methods 3 and 4) and in Method 3 Sonnet's exception re-raise path — suggesting structured prompts that encourage explicit error handling inadvertently expose stack trace information.

---

## Files Generated

| File | Contents |
|------|----------|
| `results/method1_cwe22.csv` | CWE-22 only, Method 1 |
| `results/method2_cwe22.csv` | CWE-22 only, Method 2 |
| `results/method3_sonnet_cwe22.csv` | CWE-22 only, Method 3 Sonnet |
| `results/method3_haiku_cwe22.csv` | CWE-22 only, Method 3 Haiku — **4 findings** |
| `results/method4_sonnet_cwe22.csv` | CWE-22 only, Method 4 Sonnet |
| `results/method4_haiku_cwe22.csv` | CWE-22 only, Method 4 Haiku |
| `results/method*_full.csv` | Full security-and-quality suite per method |
| `databases/method*/` | Raw CodeQL databases (for re-analysis) |
