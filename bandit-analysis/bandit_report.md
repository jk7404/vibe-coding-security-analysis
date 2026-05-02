# Bandit Static Analysis — Member 4 Complete Report

**Tool**: Bandit  
**Date**: 2026-05-02  
**Tasks analyzed**: 2 (User Profile Picture Uploader + Password Manager)  
**Methods per task**: 4 (Unconstrained, CoT, Plan-and-Solve, TDD)  
**Total codebases analyzed**: 8

---

# Task 1: User Profile Picture Uploader

## Summary

| Method | Total Issues | HIGH | MEDIUM | LOW |
|--------|:----------:|:----:|:------:|:---:|
| Method 1: Unconstrained Vibe Coding | 1 | **1** | 0 | 0 |
| Method 2: Zero-Shot CoT | 1 | **1** | 0 | 0 |
| Method 3: Plan-and-Solve | 1 | 0 | 0 | 1 |
| Method 4: TDD | 10 | **2** | 0 | 8 |

## Detailed Findings

### Method 1 — Unconstrained Vibe Coding
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`, exposing Werkzeug debugger and allowing arbitrary code execution. | 39 |

### Method 2 — Zero-Shot CoT
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`, exposing Werkzeug debugger and allowing arbitrary code execution. | 48 |

### Method 3 — Plan-and-Solve ✅ CLEANEST
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | MEDIUM | B105 | Possible hardcoded password: `'dev-secret-key-change-in-production'` | 14 |

- **Zero HIGH severity findings** — the only method to avoid `flask_debug_true`
- LOW finding is a hardcoded dev secret key, not a runtime vulnerability

### Method 4 — Test-Driven Development
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`, exposing Werkzeug debugger and allowing arbitrary code execution. | 51 |
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True` (duplicate detection across scanned copies). | 41 |
| test.py | LOW | HIGH | B101 | Use of `assert` detected — removed when compiling to optimised bytecode. | 14, 23, 24, 30 (×8 total) |

- **Note**: The majority of LOW issues originate from `test.py` (`assert` usage), not `app.py`. When filtered to `app.py` only, HIGH count = 2, LOW = 0.

---

# Task 2: Password Manager

## Summary

| Method | Total Issues | HIGH | MEDIUM | LOW |
|--------|:----------:|:----:|:------:|:---:|
| Method 1: Unconstrained Vibe Coding | 2 | **1** | 0 | 1 |
| Method 2: Zero-Shot CoT | 1 | **1** | 0 | 0 |
| Method 3: Plan-and-Solve | 2 | 0 | 0 | 2 |
| Method 4: TDD | 11 | **1** | 0 | 10 |

## Detailed Findings

### Method 1 — Unconstrained Vibe Coding
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 302 |
| utils.py | LOW | HIGH | B311 | Standard pseudo-random generator used — not suitable for cryptographic purposes. | 22 |

- **B311 notable**: use of `random` module in a password manager is a meaningful security concern.

### Method 2 — Zero-Shot CoT
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 484 |

### Method 3 — Plan-and-Solve ✅ CLEANEST
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | LOW | MEDIUM | B105 | Possible hardcoded password: `'⚠ decryption error'` | 242 |
| app.py | LOW | MEDIUM | B105 | Possible hardcoded password: `''` | 325 |

- **Zero HIGH severity findings** — both LOW findings are false positives (error message strings misidentified as passwords).

### Method 4 — Test-Driven Development
| File | Severity | Confidence | Test ID | Issue | Line |
|------|----------|------------|---------|-------|------|
| app.py | HIGH | MEDIUM | B201 | Flask app run with `debug=True`. | 320 |
| test.py | LOW | MEDIUM | B105 | Hardcoded test passwords: `'passwordB'`, `'B_SECRET_123'`, `'passwordA'`, `'password'` | 20–44 |
| test.py | LOW | HIGH | B101 | Use of `assert` detected. | 35, 36, 51 |

- **Note**: All LOW findings in `test.py` are expected test artifacts, not production vulnerabilities.

---

# Cross-Task Analysis & Synthesis

## Overall Statistics

| Metric | Profile Pic | Password Mgr | Total |
|--------|:----------:|:----------:|:-----:|
| HIGH severity issues | 4 | 3 | **7** |
| LOW severity issues | 9 | 15 | **24** |
| `flask_debug_true` (B201) | 4 | 3 | **7** |
| Hardcoded passwords (B105) | 1 | 7 | **8** |
| Insecure random (B311) | 0 | 1 | **1** |
| Assert usage (B101) | 8 | 3 | **11** |
| **Cleanest method** | M3 Plan-and-Solve | M3 Plan-and-Solve | **Both M3** |

## Key Findings

1. **`flask_debug_true` (B201) is ubiquitous**: 7 out of 8 codebases leave `debug=True` enabled. Only Plan-and-Solve avoids this across both tasks. This is the single most common HIGH severity finding.

2. **Plan-and-Solve is consistently the safest**: Zero HIGH findings in both tasks. LOW findings present are largely false positives (error message strings flagged as hardcoded passwords).

3. **TDD inflates issue counts via test files**: The majority of LOW issues in TDD methods come from `test.py` — `assert` usage (B101) and hardcoded test credentials (B105). When filtered to `app.py` only, TDD performs comparably to Vibe Coding and CoT.

4. **Unconstrained and CoT are nearly identical**: Both produce exactly 1 HIGH issue (`flask_debug_true`) per task with no other findings, suggesting CoT reasoning steps provide minimal additional security benefit at the Bandit analysis level.

5. **B311 in Password Manager Method 1**: Use of a non-cryptographic random generator in a password manager is a meaningful finding beyond debug mode — the only crypto-specific issue Bandit detected.

## Prompting Strategy Effectiveness (Bandit)

| Strategy | HIGH Findings | LOW Findings | Notable Issues |
|----------|:----------:|:----------:|----------------|
| Unconstrained | 2 | 1 | `debug=True`, weak random |
| Chain-of-Thought | 2 | 0 | `debug=True` only |
| Plan-and-Solve | **0** | 4 | False positive B105 only |
| Test-Driven Dev | 3 | 18 | `debug=True` + test artifacts |

## Limitations of Bandit Analysis

- **No taint tracking**: Bandit cannot detect CWE-22 path traversal via data flow. This is covered by Member 3's CodeQL analysis.
- **AST-only**: Pattern-based detection means false positives (e.g., error message strings flagged as B105).
- **Test file noise**: B101 (`assert`) and B105 (hardcoded test credentials) inflate TDD issue counts without reflecting production security quality.

---

## Generated Files
- `results_uploader_{vibe,cot,pns,tdd}.json` — Raw Bandit JSON per method (uploader)
- `results_pm_{vibe,cot,pns,tdd}.json` — Raw Bandit JSON per method (password manager)
- `summary.csv` — Aggregated issue counts by task and method
- `detailed_results.csv` — Full issue-level detail with severity, test ID, and issue text
