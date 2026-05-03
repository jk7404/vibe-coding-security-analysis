# Server Log Manager Analysis (Task 3/3)

**Date**: 2026-05-03  
**Analyzed**: 3 models with unconstrained vibe coding approach  
**Models**: Gemma4, GPT5.2, Haiku4.5

---

## CWE-22 Path Traversal Findings

| Model | CWE-22 | Severity |
|-------|:------:|----------|
| Gemma4 | **1** | Medium — Path expression on log filename |
| GPT5.2 | **0** | — |
| Haiku4.5 | **4** | High — Multiple path expressions on log operations |

---

## Security Findings Summary

| Model | Debug Mode | CWE-22 | CWE-78 (Cmd) | Info Disc | Uninitialized Vars | Other | Total |
|-------|:----------:|:------:|:----------:|:--------:|:--:|:------:|:-----:|
| Gemma4 | 1 | 1 | 0 | 0 | 0 | 1 unused import | **3** |
| GPT5.2 | 1 | 0 | 1 | 0 | 3 | 0 | **5** |
| Haiku4.5 | 0 | 4 | 0 | 2 | 0 | 1 BaseException | **7** |

---

## Detailed Findings

### Gemma4 (3 findings)
- **Debug mode** (`app.py:65`): `app.run(debug=True)`
- **CWE-22** (`app.py:33`): Path expression depends on user-provided value at line 2:43
- **Unused import** (`app.py:2`): `Response` not used

### GPT5.2 (5 findings) ⚠️ NEW: CWE-78
- **Debug mode** (`app.py:172`): `app.run(debug=True)`
- **CWE-78 Command Injection** (`app.py:135`): Command line depends on user-provided value at line 7:60
  - This is a NEW vulnerability type (not seen in Tasks 1-2)
- **Uninitialized variables** (`app.py`):
  - `size` may be used before init (line 60)
  - `data` may be used before init (line 71)
  - `completed` may be used before init (line 148)

### Haiku4.5 (7 findings) ⚠️ HIGHEST RISK
- **CWE-22 × 4** (`log_viewer.py`):
  - Line 152: Path depends on user-provided value (line 1:50-1:56)
  - Line 175: Path depends on user-provided value
  - Line 178: Path depends on user-provided value
  - Line 182: Path depends on user-provided value
- **Information exposure × 2** (`log_viewer.py`):
  - Line 187: Exception stack trace exposed to external user
  - Line 216: Exception stack trace exposed
- **BaseException handling** (`log_viewer.py:154`): Catches BaseException, may mis-handle system exits/keyboard interrupts

---

## Cross-All-Tasks Summary

| Task | Model | CWE-22 | Debug | Other Issues | Total |
|------|:-----:|:------:|:-----:|:----------:|:-----:|
| **Profile Pic** | M3 Haiku | 4 | 0 | 4 (info+imports) | **8** |
| **Profile Pic** | M1 Sonnet | 0 | 1 | 1 (debug) | **1** |
| **Password Mgr** | M1 Unconstrained | 0 | 1 | 2 (imports+mixed ret) | **3** |
| **Password Mgr** | M3 (P&S) | 0 | 0 | 0 | **0** ✅ |
| **Server Logs** | Gemma4 | 1 | 1 | 1 (import) | **3** |
| **Server Logs** | GPT5.2 | 0 | 1 | 4 (CWE-78 + uninit vars) | **5** |
| **Server Logs** | Haiku4.5 | 4 | 0 | 3 (info + BaseExc) | **7** |

---

## Key Patterns Across All Tasks

1. **Haiku model consistently vulnerable** (Unconstrained approach):
   - Profile Pic Haiku: 4 CWE-22
   - Server Logs Haiku: 4 CWE-22 + 2 info disclosure
   - Total Haiku findings: 8 vulnerabilities

2. **GPT5.2 introduces new vulnerability class**:
   - First and only CWE-78 (Command Injection) detected
   - Also first to have uninitialized variable errors
   - Suggests GPT5.2 may generate more complex (but buggy) code

3. **Unconstrained vibe coding risk profile**:
   - CWE-22: 5 findings total (1 Gemma + 4 Haiku)
   - Debug mode: 7/15 codebases leave debug=True
   - Highest severity: Server Logs Haiku (7 findings)

4. **Model-specific patterns**:
   - **Gemma4**: Balanced (CWE-22 + debug + minor issues)
   - **GPT5.2**: Logic errors over path traversal (uninitialized vars, command injection)
   - **Haiku4.5**: Severe path traversal + info disclosure

---

## Tasks 1-3 Aggregate Statistics

| Metric | Value |
|--------|:-----:|
| Total codebases analyzed | 15 |
| Total CWE-22 findings | 9 |
| Total debug mode issues | 11 |
| Total info disclosure | 5 |
| Total CWE-78 (cmd injection) | 1 |
| Total other findings | 8 |
| **GRAND TOTAL** | **34 security/quality findings** |

**Most vulnerable codebase**: Profile Pic M3 Haiku + Server Logs Haiku (8 + 7 = 15 findings combined)  
**Cleanest codebase**: Password Manager M3 (Plan-and-Solve) — 0 findings
