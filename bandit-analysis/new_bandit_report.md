# Bandit Static Analysis — Member 4 Complete Report

**Tool**: Bandit  
**Date**: 2026-05-02  
**Tasks analyzed**: 3 (User Profile Picture Uploader + Password Manager + Server Log Manager)  
**Models evaluated**: GPT-5.2, Claude Haiku 4.5  
**Methods per task**: 4 (Unconstrained, CoT, Plan-and-Solve, TDD)  
**Total codebases analyzed**: 24

---

# Task 1: User Profile Picture Uploader

## Summary

| Method | Model | Total Issues | HIGH | MEDIUM | LOW |
|--------|-------|:----------:|:----:|:------:|:---:|
| Unconstrained | GPT-5.2 | 1 | **1** | 0 | 0 |
| Unconstrained | Haiku 4.5 | 1 | **1** | 0 | 0 |
| CoT | GPT-5.2 | 0 | 0 | 0 | 0 |
| CoT | Haiku 4.5 | 1 | **1** | 0 | 0 |
| Plan-and-Solve | GPT-5.2 | 0 | 0 | 0 | 0 |
| Plan-and-Solve | Haiku 4.5 | 0 | 0 | 0 | 0 |
| TDD | GPT-5.2 | 10 | 0 | 0 | 10 |
| TDD | Haiku 4.5 | 10 | 0 | 0 | 10 |

## Detailed Findings

### Unconstrained — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`, exposing Werkzeug debugger and allowing arbitrary code execution. | 182 |

### Unconstrained — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`, exposing Werkzeug debugger and allowing arbitrary code execution. | 57 |

### CoT — GPT-5.2 ✅ CLEAN
- Zero findings.

### CoT — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 71 |

### Plan-and-Solve — GPT-5.2 ✅ CLEAN
- Zero findings.

### Plan-and-Solve — Haiku 4.5 ✅ CLEAN
- Zero findings.

### TDD — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| test.py | LOW | HIGH | B101 | Use of `assert` detected — removed when compiling to optimised bytecode. | 20, 21, 30, 44, 45, 56, 57, 68, 69, 76 |

- **Note**: All 10 issues are from `test.py` only. `app.py` is clean.

### TDD — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| test.py | LOW | HIGH | B101 | Use of `assert` detected — removed when compiling to optimised bytecode. | 20, 21, 30, 44, 45, 56, 57, 68, 69, 76 |

- **Note**: Identical findings to GPT-5.2 TDD — same `test.py` used across both models.

---

# Task 2: Password Manager

## Summary

| Method | Model | Total Issues | HIGH | MEDIUM | LOW |
|--------|-------|:----------:|:----:|:------:|:---:|
| Unconstrained | GPT-5.2 | 1 | **1** | 0 | 0 |
| Unconstrained | Haiku 4.5 | 1 | **1** | 0 | 0 |
| CoT | GPT-5.2 | 1 | **1** | 0 | 0 |
| CoT | Haiku 4.5 | 8 | 0 | 0 | 8 |
| Plan-and-Solve | GPT-5.2 | 1 | 0 | 0 | 1 |
| Plan-and-Solve | Haiku 4.5 | 15 | 0 | 0 | 15 |
| TDD | GPT-5.2 | 24 | 0 | 0 | 24 |
| TDD | Haiku 4.5 | 24 | 0 | 0 | 24 |

## Detailed Findings

### Unconstrained — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 260 |

### Unconstrained — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 226 |

### CoT — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 350 |

### CoT — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| test_functionality.py | LOW | MEDIUM | B105 | Hardcoded test passwords: `'test_master_pass_123'`, `'super_secret_password_123'` | 20, 40 |
| test_functionality.py | LOW | HIGH | B101 | Use of `assert` detected. | 34, 57, 61, 74, 78, 82 |

- **Note**: Zero HIGH findings. All issues from test file — expected test artifacts.

### Plan-and-Solve — GPT-5.2 ✅ CLEANEST
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | MEDIUM | B105 | Possible hardcoded password: `'[Decryption failed]'` | 441 |

- **False positive**: error message string misidentified as a password. Zero genuine findings.

### Plan-and-Solve — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| test_app.py | LOW | MEDIUM | B105 | Hardcoded test passwords (×14): `'SecurePass123!'`, `'MyGmailPassword123!'`, `'wrongpassword'`, etc. | 33–256 |

- **Note**: All 15 issues from `test_app.py` — false positives from test credentials. `app.py` is clean.

### TDD — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| test.py | LOW | MEDIUM | B105 | Hardcoded test passwords (×11): `'password123'`, `'alicepassword'`, `'super-secret-123'`, etc. | 23–101 |
| test.py | LOW | HIGH | B101 | Use of `assert` detected (×9). | 24–109 |

- **Note**: All 24 issues from `test.py`. `app.py` is clean. Same findings for both models.

### TDD — Haiku 4.5
- Identical findings to GPT-5.2 TDD — same `test.py` shared across models.

---

# Task 3: Server Log Manager

## Summary

| Method | Model | Total Issues | HIGH | MEDIUM | LOW |
|--------|-------|:----------:|:----:|:------:|:---:|
| Unconstrained | GPT-5.2 | 3 | **1** | 0 | 2 |
| Unconstrained | Haiku 4.5 | 3 | 0 | 0 | 3 |
| CoT | GPT-5.2 | 3 | 0 | 0 | 3 |
| CoT | Haiku 4.5 | 4 | **1** | 0 | 3 |
| Plan-and-Solve | GPT-5.2 | 2 | 0 | 0 | 2 |
| Plan-and-Solve | Haiku 4.5 | 3 | 0 | 0 | 3 |
| TDD | GPT-5.2 | 6 | 0 | 0 | 6 |
| TDD | Haiku 4.5 | 7 | 0 | 0 | 7 |

## Detailed Findings

### Unconstrained — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 172 |
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 3 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 134 |

### Unconstrained — Haiku 4.5 ✅ NO HIGH
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| log_viewer.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 3 |
| log_viewer.py | LOW | HIGH | B607 | Starting a process with a partial executable path. | 201 |
| log_viewer.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 201 |

### CoT — GPT-5.2 ✅ NO HIGH
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 2 |
| app.py | LOW | HIGH | B112 | Try, Except, Continue detected. | 56 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 119 |

### CoT — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 102 |
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 2 |
| app.py | LOW | HIGH | B607 | Starting a process with a partial executable path. | 80 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 80 |

### Plan-and-Solve — GPT-5.2 ✅ CLEANEST
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 3 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 120 |

- Zero HIGH findings. Subprocess used safely without `shell=True`.

### Plan-and-Solve — Haiku 4.5 ✅ NO HIGH
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 3 |
| app.py | LOW | HIGH | B607 | Starting a process with a partial executable path. | 102 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 102 |

### TDD — GPT-5.2
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 6 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 63 |
| test.py | LOW | HIGH | B101 | Use of `assert` detected. | 13, 14, 24, 28 |

### TDD — Haiku 4.5
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | HIGH | B404 | Consider security implications of the `subprocess` module. | 3 |
| app.py | LOW | HIGH | B607 | Starting a process with a partial executable path. | 119 |
| app.py | LOW | HIGH | B603 | Subprocess call — check for execution of untrusted input. | 119 |
| test.py | LOW | HIGH | B101 | Use of `assert` detected. | 13, 14, 24, 28 |

---

# Cross-Task Analysis & Synthesis

## Overall HIGH Severity Findings by Method & Model

| Task | Method | GPT-5.2 HIGH | Haiku 4.5 HIGH |
|------|--------|:------------:|:--------------:|
| Uploader | Unconstrained | 1 | 1 |
| Uploader | CoT | 0 ✅ | 1 |
| Uploader | Plan-and-Solve | 0 ✅ | 0 ✅ |
| Uploader | TDD | 0 ✅ | 0 ✅ |
| Password Manager | Unconstrained | 1 | 1 |
| Password Manager | CoT | 1 | 0 ✅ |
| Password Manager | Plan-and-Solve | 0 ✅ | 0 ✅ |
| Password Manager | TDD | 0 ✅ | 0 ✅ |
| Server Log Manager | Unconstrained | 1 | 0 ✅ |
| Server Log Manager | CoT | 0 ✅ | 1 |
| Server Log Manager | Plan-and-Solve | 0 ✅ | 0 ✅ |
| Server Log Manager | TDD | 0 ✅ | 0 ✅ |

## Key Findings

1. **Plan-and-Solve achieves zero HIGH findings across all tasks and both models** — the only method to do so consistently. Structured architectural planning effectively eliminates the most common HIGH severity issues.

2. **TDD produces zero HIGH findings in `app.py`** — all HIGH/LOW issues from TDD come exclusively from test files (`test.py`, `test_functionality.py`). When filtered to production code only, TDD is as safe as Plan-and-Solve.

3. **`flask_debug_true` (B201) remains the dominant HIGH finding** — present in Unconstrained across all tasks and both models, and sporadically in CoT. It is entirely absent from Plan-and-Solve outputs.

4. **Model differences are inconsistent**: GPT-5.2 and Haiku 4.5 do not show a clear winner. For example, CoT GPT-5.2 is clean on the uploader while Haiku 4.5 is not; but for the password manager, CoT Haiku 4.5 is cleaner. Neither model consistently outperforms the other.

5. **Server Log Manager introduces subprocess-specific risks**: Unlike the other two tasks, all codebases use the `subprocess` module — introducing B404, B603, and B607 warnings. However, no `shell=True` (B605) was detected, unlike the earlier Gemma4 result, suggesting GPT-5.2 and Haiku 4.5 are more security-aware with subprocess usage.

6. **Test file noise inflates TDD and CoT Haiku issue counts**: B101 (`assert`) and B105 (hardcoded test credentials) are test artifacts, not production vulnerabilities. Raw issue counts without filtering are misleading for TDD evaluation.

## Prompting Strategy Effectiveness Summary

| Strategy | Total HIGH (all tasks, both models) | HIGH in `app.py` only | Overall Assessment |
|----------|:-----------------------------------:|:---------------------:|-------------------|
| Unconstrained | 5 | 5 | ⭐⭐ Most risky |
| CoT | 2 | 2 | ⭐⭐⭐ Mixed results |
| Plan-and-Solve | **0** | **0** | ⭐⭐⭐⭐⭐ Consistently safest |
| TDD | 0 | **0** | ⭐⭐⭐⭐ Safe in production code |

## Limitations of Bandit Analysis

- **No taint tracking**: Bandit cannot detect CWE-22 path traversal via data flow. This is covered by Member 3's CodeQL analysis.
- **AST-only**: Pattern-based detection produces false positives (e.g., error message strings flagged as B105 hardcoded passwords).
- **Test file noise**: B101 (`assert`) and B105 (hardcoded test credentials) inflate TDD and CoT Haiku issue counts without reflecting production security quality.
- **Subprocess warnings are informational**: B404, B603, B607 are advisory LOW warnings — not confirmed vulnerabilities. Exploitability depends on whether user input actually reaches the subprocess call.

---

## Generated Files
- `results_uploader2_{vibe,cot,pns,tdd}_{gpt5,haiku}.json` — Raw Bandit JSON per method/model (uploader)
- `results_pm2_{vibe,cot,pns,tdd}_{gpt5,haiku}.json` — Raw Bandit JSON per method/model (password manager)
- `results_slm2_{vibe,cot,pns,tdd}_{gpt5,haiku}.json` — Raw Bandit JSON per method/model (server log manager)
- `summary2.csv` — Aggregated issue counts by task, method, and model
- `detailed_results2.csv` — Full issue-level detail with severity, test ID, and issue text