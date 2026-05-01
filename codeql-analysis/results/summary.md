# CodeQL Security Analysis — Member 3 Complete Report

**Tool**: CodeQL 2.24.0  
**Query pack**: `codeql/python-queries@1.8.1`  
**Suites run**:
- CWE-22: `Security/CWE-022/PathInjection.ql`
- Full suite: `python-security-and-quality.qls`

**Date**: 2026-05-01  
**Tasks analyzed**: 2 (User Profile Picture Uploader + Password Manager)  
**Methods per task**: 4 (Unconstrained, CoT, Plan-and-Solve, TDD)  
**Total codebases analyzed**: 8

---

# Task 1: User Profile Picture Uploader

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

---

# Task 2: Password Manager

## CWE-22 Path Traversal Findings

| Method | Model | CWE-22 | Result |
|--------|-------|:------:|--------|
| Password Manager Method 1 | Unconstrained | **0** | ✅ No path traversal |
| Password Manager Method 2 | CoT | **0** | ✅ No path traversal |
| Password Manager Method 3 | Plan-and-Solve | **0** | ✅ No path traversal |
| Password Manager Method 4 | TDD | **0** | ✅ No path traversal |

## All Security Findings (Error Severity)

| Method | Debug Mode | Unused Imports | Mixed Returns | Total |
|--------|:----------:|:--------------:|:--------------:|:-----:|
| Method 1: Unconstrained | 1 | 1 | 1 | **3** |
| Method 2: CoT | 1 | 3 | 0 | **4** |
| Method 3: Plan-and-Solve | 0 | 0 | 0 | **0** ✅ |
| Method 4: TDD | 1 | 1 | 0 | **2** |

## Detailed Findings

### Password Manager Method 1: Unconstrained
- **Debug mode** (`app.py:302`): `app.run(debug=True)`
- **Unused import** (`app.py:3`): `derive_key` not used
- **Mixed returns** (`app.py:276`): Function mixes implicit (None) and explicit returns

### Password Manager Method 2: CoT
- **Debug mode** (`app.py:484`): `app.run(debug=True)`
- **Unused imports** (`app.py`): `hashlib`, `hmac`, `datetime` — imported but not used
  - Suggests the LLM anticipated needs without following through

### Password Manager Method 3: Plan-and-Solve ✅ CLEANEST
- **Zero findings** — No CWE-22, no debug mode, no unused imports
- Most security-conscious and code-quality implementation

### Password Manager Method 4: TDD
- **Debug mode** (`app.py:320`): `app.run(debug=True)`
- **Unused import** (`test.py:2`): `io` module not used

---

# Cross-Task Analysis & Synthesis

## Overall Statistics

| Metric | Profile Pic | Password Mgr | Total |
|--------|:----------:|:----------:|:-----:|
| CWE-22 vulnerabilities | 4 | 0 | **4** |
| Debug mode issues | 4 | 3 | **7** |
| Info disclosure | 3 | 0 | **3** |
| Unused imports/vars | 4 | 5 | **9** |
| **Total findings** | **11** | **9** | **20** |
| **Cleanest method** | M3 Sonnet | M3 | Both M3 |

## Key Cross-Task Insights

1. **Plan-and-Solve dominates**: Method 3 (Plan-and-Solve) is consistently the cleanest across both tasks
   - Profile Pic: Strong (no CWE-22)
   - Password Manager: Excellent (zero findings)
   - Hypothesis: Structured prompting with explicit architectural planning prevents both vulnerabilities and code quality issues.

2. **CWE-22 is task-specific**: 
   - Task 1 (file operations): 4 findings in M3 Haiku (new attack surface from serving endpoint)
   - Task 2 (crypto operations): 0 findings across all methods (no file path operations)

3. **Debug mode is ubiquitous risk**:
   - 7 out of 8 codebases leave `debug=True`
   - Pattern: Unconstrained, CoT, TDD all fail here
   - Only Plan-and-Solve methods consistently disable debug mode

4. **Unconstrained and CoT over-import**:
   - Unconstrained: Adds unnecessary utility functions (mixed returns)
   - CoT: Imports 3 unused standard library modules
   - Suggests these prompts cause the LLM to speculate about needs

5. **Information disclosure pattern**:
   - Only appears in Profile Pic task (3 findings)
   - All expose `str(exception)` in HTTP responses
   - Haiku and structured methods both guilty

## Prompting Strategy Effectiveness

| Strategy | CWE-22 Risk | Code Quality | Overall Score |
|----------|:----------:|:----------:|:----------:|
| Unconstrained | Medium | Low | ⭐⭐ |
| Chain-of-Thought | Low | Low | ⭐⭐ |
| Plan-and-Solve | **Low** | **High** | **⭐⭐⭐⭐⭐** |
| Test-Driven Dev | Low | Medium | ⭐⭐⭐ |

---

## Generated Files

### Task 1: User Profile Picture Uploader
- `method{1,2}_cwe22.csv` — Vibe Coding, CoT CWE-22 (0 findings each)
- `method3_{sonnet,haiku}_cwe22.csv` — Plan-and-Solve variants (0, **4** findings)
- `method4_{sonnet,haiku}_cwe22.csv` — TDD variants (0 findings each)
- `method{1,2,3_sonnet,3_haiku,4_sonnet,4_haiku}_full.csv` — Full security suite results

### Task 2: Password Manager
- `pm_method{1,2,3,4}_cwe22.csv` — All CWE-22 analyses (0 findings each)
- `pm_method{1,2,3,4}_full.csv` — Full security suite results

### Infrastructure
- `databases/method*/`, `databases/pm_method*/` — CodeQL databases (excluded from git)
- `sources/{method,pm_method}*/` — Analyzed source copies (excluded from git)
