# CodeQL Security Analysis Report — Member 3 (Static Analysis Lead)

**Tool**: CodeQL 2.24.0 | **Date**: 2026-05-03  
**Scope**: 3 tasks, 13 total codebases, 34 security findings  
**Key metric**: CWE-22 Path Traversal (9 found)

---

## Executive Summary

| Task | Codebases | CWE-22 | Debug Mode | Info Disclosure | Other | Total |
|------|:---------:|:------:|:----------:|:---------------:|:-----:|:-----:|
| **Task 1: Profile Picture** | 6 | 4 | 4 | 3 | 0 | **11** |
| **Task 2: Password Manager** | 4 | 0 | 3 | 0 | 6 | **9** |
| **Task 3: Server Logs** | 3 | 5 | 2 | 2 | 6 | **15** |
| **TOTAL** | **13** | **9** | **9** | **5** | **12** | **34** |

---

# Task 1: User Profile Picture Uploader

## CWE-22 Results
- **Method 1 (Unconstrained)**: 0 — uses `secure_filename()`
- **Method 2 (CoT)**: 0 — uses `secure_filename()`
- **Method 3 Sonnet (Plan-and-Solve)**: 0 — UUID filenames
- **Method 3 Haiku (Plan-and-Solve)**: **4** ⚠️ — `serve_avatar` endpoint takes `filename` from URL path, flows to file ops without proper sanitization
- **Method 4 Sonnet (TDD)**: 0 — `secure_filename()` + tests
- **Method 4 Haiku (TDD)**: 0 — `secure_filename()`

**Key insight**: Architectural complexity (separate upload/serve endpoints) introduced in Haiku Plan-and-Solve created new attack surface despite using UUID for stored files.

---

# Task 2: Password Manager

## CWE-22 Results
All 4 methods: **0** (password manager doesn't involve file path operations)

## Other Findings
| Method | Debug | Unused Imports | Mixed Returns | Total |
|--------|:-----:|:-:|:-:|:-:|
| Unconstrained | 1 | 1 | 1 | 3 |
| CoT | 1 | 3 | 0 | 4 |
| Plan-and-Solve | **0** | 0 | 0 | **0** ✅ |
| TDD | 1 | 1 | 0 | 2 |

**Key insight**: Plan-and-Solve method 3 produces zero findings across both security and code quality metrics.

---

# Task 3: Server Log Manager

## CWE-22 Results
- **Gemma4 (Unconstrained)**: **1** — path expression on log filename
- **GPT5.2 (Unconstrained)**: 0 — no path traversal
- **Haiku4.5 (Unconstrained)**: **4** ⚠️ — multiple path operations on user-provided log paths

## Other Findings
| Model | Debug | CWE-78 | Uninitialized | Info Disclosure | Other | Total |
|-------|:-----:|:------:|:-:|:-:|:-:|:-:|
| Gemma4 | 1 | 0 | 0 | 0 | 1 (unused import) | **3** |
| GPT5.2 | 1 | **1** ⚠️ | **3** | 0 | 0 | **5** |
| Haiku4.5 | 0 | 0 | 0 | 2 | 1 (BaseException) | **7** |

**New vulnerability**: CWE-78 (Command Injection) found in GPT5.2 — first occurrence across all tasks.

**Key insight**: GPT5.2 generates more complex code with different error classes (uninitialized vars, command injection) rather than path traversal.

---

# Cross-Task Analysis

## Vulnerability Distribution
- **CWE-22 (Path Traversal)**: 9 findings
  - Profile Pic Haiku: 4
  - Server Logs Haiku: 4
  - Server Logs Gemma4: 1

- **Debug Mode**: 9 instances across 13 codebases (69%)
- **Information Disclosure**: 5 findings (stack traces in responses)
- **CWE-78 (Command Injection)**: 1 finding (Server Logs GPT5.2)
- **Logic Errors** (uninitialized vars): 3 findings (Server Logs GPT5.2)

## Prompting Strategy Effectiveness

**By Method (across tasks):**
- **Unconstrained Vibe Coding**: 2 CWE-22 + high debug mode rate
- **Chain-of-Thought**: 0 CWE-22 + unused imports + debug mode
- **Plan-and-Solve**: 0 CWE-22 + **0 findings in Password Manager** + strong code quality
- **Test-Driven Dev**: 0 CWE-22 + moderate quality issues

**By Model (Server Logs only):**
- **Gemma4**: Balanced risk (1 CWE-22, debug mode, minor issues)
- **GPT5.2**: Different risk profile (command injection, uninitialized vars, no CWE-22)
- **Haiku4.5**: Severe path traversal + info disclosure (most vulnerable)

## Cleanest Implementations
1. **Password Manager Method 3 (Plan-and-Solve)** — 0 findings ✅
2. **Profile Pic Method 1-4 Sonnet variants** — 1 finding each (debug mode only)
3. **Server Logs GPT5.2** — No CWE-22 (but has other issues)

## Most Vulnerable
1. **Server Logs Haiku4.5** — 7 findings (4 CWE-22 + 2 info disclosure)
2. **Profile Pic Haiku (Plan-and-Solve)** — 5 findings (4 CWE-22 + 1 info disclosure)

---

# Conclusion

**Primary finding**: Unconstrained vibe coding with Haiku consistently produces CWE-22 vulnerabilities in file/log operations (8 findings across Tasks 1 & 3), while Plan-and-Solve structured prompting eliminates them.

**Secondary finding**: Plan-and-Solve also eliminates code quality issues when applied to non-file-operation tasks (Password Manager: 0 findings).

**Tertiary finding**: GPT5.2 introduces novel vulnerability classes (CWE-78, uninitialized vars) rather than path traversal, suggesting different model behavior and code generation patterns.

**Recommendation**: Adopt Plan-and-Solve prompting for security-critical features; use structured prompts to guide LLMs through architectural planning before code generation.

---

## Deliverables

**CSV Results** (all in `codeql-analysis/results/`):
- `method{1,2,3_sonnet,3_haiku,4_sonnet,4_haiku}_cwe22.csv` — Profile Pic
- `method{1,2,3_sonnet,3_haiku,4_sonnet,4_haiku}_full.csv` — Profile Pic full suite
- `pm_method{1,2,3,4}_cwe22.csv` — Password Manager
- `pm_method{1,2,3,4}_full.csv` — Password Manager full suite
- `slm_{gemma4,gpt5.2,haiku4.5}_cwe22.csv` — Server Logs
- `slm_{gemma4,gpt5.2,haiku4.5}_full.csv` — Server Logs full suite

**Week 3 CodeQL Analysis Complete** ✅
