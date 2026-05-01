# CodeQL Analysis — Password Manager (Task 2/3)

**Date**: 2026-05-01  
**Analyzed**: 4 password manager implementations (Unconstrained, CoT, Plan-and-Solve, TDD)

---

## Summary: CWE-22 Path Traversal Findings

| Method | Model | CWE-22 | Result |
|--------|-------|:------:|--------|
| Password Manager Method 1 | Unconstrained | **0** | ✅ No path traversal |
| Password Manager Method 2 | CoT | **0** | ✅ No path traversal |
| Password Manager Method 3 | Plan-and-Solve | **0** | ✅ No path traversal |
| Password Manager Method 4 | TDD | **0** | ✅ No path traversal |

---

## All Security Findings (Error Severity)

| Method | Debug Mode | Unused Imports | Mixed Returns | Total |
|--------|:----------:|:--------------:|:--------------:|:-----:|
| Method 1: Unconstrained | 1 | 1 | 1 | **3** |
| Method 2: CoT | 1 | 3 | 0 | **4** |
| Method 3: Plan-and-Solve | 0 | 0 | 0 | **0** ✅ |
| Method 4: TDD | 1 | 1 | 0 | **2** |

---

## Detailed Findings

### Method 1: Unconstrained
- **Debug mode** (`app.py:302`): `app.run(debug=True)`
- **Unused import** (`app.py:3`): `derive_key` not used
- **Mixed returns** (`app.py:276`): Function mixes implicit (None) and explicit returns

### Method 2: CoT
- **Debug mode** (`app.py:484`): `app.run(debug=True)`
- **Unused imports** (`app.py`): `hashlib`, `hmac`, `datetime` imported but not used
  - Suggests the LLM imported standard modules it didn't need

### Method 3: Plan-and-Solve ✅ CLEANEST
- **Zero findings** — No CWE-22, no debug mode, no unused imports
- Most security-conscious and code-quality implementation

### Method 4: TDD
- **Debug mode** (`app.py:320`): `app.run(debug=True)`
- **Unused import** (`test.py:2`): `io` module not used

---

## Key Insights

1. **CWE-22 not applicable**: Password manager doesn't involve file path operations (unlike profile picture uploader). No taint paths from user input to file system.

2. **Plan-and-Solve excels again**: Method 3 produces zero security and quality findings — structured prompting with explicit architecture planning prevents both vulnerabilities and code quality issues.

3. **Debug mode is ubiquitous**: Methods 1, 2, 4 all leave `debug=True`, a high-severity misconfiguration.

4. **Unconstrained approach adds complexity**: Method 1 (Unconstrained) introduces unnecessary utility functions (mixed returns) and unused imports, hinting at less rigorous design.

5. **CoT over-imports**: Method 2 imports 3 standard library modules it never uses, suggesting the CoT model anticipates needs without actually following through.

---

## Comparison with User Profile Picture Uploader

| Metric | Profile Pic (CWE-22 task) | Password Manager |
|--------|:------------------------:|:---------------:|
| CWE-22 found | 4 (Method 3 Haiku) | 0 (all methods) |
| Cleanest method | Method 3 Sonnet | Method 3 |
| Debug mode issues | 4 methods | 3 methods |
| Plan-and-Solve strength | Strong (no CWE-22) | Excellent (zero findings) |

---

## Files

- `pm_method1_cwe22.csv` — CWE-22 analysis (0 findings)
- `pm_method2_cwe22.csv` — CWE-22 analysis (0 findings)
- `pm_method3_cwe22.csv` — CWE-22 analysis (0 findings)
- `pm_method4_cwe22.csv` — CWE-22 analysis (0 findings)
- `pm_method1_full.csv` — Full security suite (3 findings)
- `pm_method2_full.csv` — Full security suite (4 findings)
- `pm_method3_full.csv` — Full security suite (0 findings)
- `pm_method4_full.csv` — Full security suite (2 findings)
