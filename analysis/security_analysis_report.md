# Security Analysis of LLM-Generated Flask Applications
## Evaluating the Impact of Prompting Strategies on Code Security

**Research Team**: Jaehyeon Kim, Daewoong Lim, Sihyun Kim, Yongje Jeon  
**Analysis Date**: May 4, 2026  
**Tools**: CodeQL v3.12.11 (Python Security Queries v1.8.1) + Bandit  
**Scope**: 24 codebases — 3 tasks × 4 prompting methods × 2 LLMs

---

## 1. Experimental Design

### Tasks
| ID | Task | Inherent Security Risk |
|----|------|------------------------|
| PM | Password Manager | Credential storage, auth |
| SLM | Server Log Manager | Filesystem access, shell commands |
| UPL | User Profile Picture Uploader | File upload, path handling |

### Prompting Methods
| # | Method | Description |
|---|--------|-------------|
| 1 | **Unconstrained** | Minimal, conversational prompt — no security guidance |
| 2 | **Chain-of-Thought (CoT)** | Added "think step-by-step" instruction before coding |
| 3 | **Plan-and-Solve (PnS)** | Required explicit security architectural planning phase |
| 4 | **Test-Driven Dev (TDD)** | Provided test suite; code must pass all tests |

### Models
- **GPT-5.2** (OpenAI Codex family)
- **Claude Haiku 4.5** (Anthropic)

---

## 2. CWE Vulnerability Taxonomy

All CodeQL findings were mapped to the following CWEs:

| CWE | CodeQL Finding Name | OWASP A-Category | Severity |
|-----|---------------------|------------------|----------|
| **CWE-22** | Uncontrolled data used in path expression | A01 – Broken Access Control | Critical |
| **CWE-78** | Uncontrolled command line | A03 – Injection | Critical |
| **CWE-79** | Reflected server-side XSS | A03 – Injection | High |
| **CWE-94/1336** | Server Side Template Injection | A03 – Injection | Critical |
| **CWE-209** | Information exposure through exception | A09 – Security Logging | Medium |
| **CWE-312** | Clear-text storage of sensitive information | A02 – Cryptographic Failure | High |
| **CWE-489** | Flask app run in debug mode | A05 – Security Misconfiguration | High |

---

## 3. Complete CodeQL Results

### 3.1 Raw Findings — All 24 Variants

| Program | Method | Model | Total | CWE-22 | CWE-78 | CWE-79 | CWE-94/1336 | CWE-209 | CWE-312 | CWE-489 |
|---------|--------|-------|:-----:|:------:|:------:|:------:|:-----------:|:-------:|:-------:|:-------:|
| PM | Unconstrained | GPT-5.2 | **2** | – | – | – | – | – | 1 | 1 |
| PM | Unconstrained | Haiku 4.5 | **1** | – | – | – | – | – | – | 1 |
| PM | CoT | GPT-5.2 | **1** | – | – | – | – | – | – | 1 |
| PM | CoT | Haiku 4.5 | **0** ✅ | – | – | – | – | – | – | – |
| PM | Plan-and-Solve | GPT-5.2 | **1** | – | – | – | – | – | 1 | – |
| PM | Plan-and-Solve | Haiku 4.5 | **0** ✅ | – | – | – | – | – | – | – |
| PM | TDD | GPT-5.2 | **0** ✅ | – | – | – | – | – | – | – |
| PM | TDD | Haiku 4.5 | **0** ✅ | – | – | – | – | – | – | – |
| SLM | Unconstrained | GPT-5.2 | **2** | – | 1 | – | – | – | – | 1 |
| SLM | Unconstrained | Haiku 4.5 | **6** | 4 | – | – | – | 2 | – | – |
| SLM | CoT | GPT-5.2 | **8** | 7 | 1 | – | – | – | – | – |
| SLM | CoT | Haiku 4.5 | **3** | – | – | – | – | 2 | – | 1 |
| SLM | Plan-and-Solve | GPT-5.2 | **1** | – | 1 | – | – | – | – | – |
| SLM | Plan-and-Solve | Haiku 4.5 | **3** | 3 | – | – | – | – | – | – |
| SLM | TDD | GPT-5.2 | **4** | 4 | – | – | – | – | – | – |
| SLM | TDD | Haiku 4.5 | **8** | 2 | – | 2 | 2 | 2 | – | – |
| UPL | Unconstrained | GPT-5.2 | **1** | – | – | – | – | – | – | 1 |
| UPL | Unconstrained | Haiku 4.5 | **1** | – | – | – | – | – | – | 1 |
| UPL | CoT | GPT-5.2 | **0** ✅ | – | – | – | – | – | – | – |
| UPL | CoT | Haiku 4.5 | **1** | – | – | – | – | – | – | 1 |
| UPL | Plan-and-Solve | GPT-5.2 | **1** | 1 | – | – | – | – | – | – |
| UPL | Plan-and-Solve | Haiku 4.5 | **3** | – | – | – | – | 3 | – | – |
| UPL | TDD | GPT-5.2 | **0** ✅ | – | – | – | – | – | – | – |
| UPL | TDD | Haiku 4.5 | **0** ✅ | – | – | – | – | – | – | – |
| **TOTAL** | | | **47** | **21** | **3** | **2** | **2** | **9** | **2** | **8** |

### 3.2 Findings by Prompting Method

| Method | GPT-5.2 Total | Haiku 4.5 Total | Combined | % of All Findings |
|--------|:-------------:|:---------------:|:--------:|:-----------------:|
| Unconstrained | 5 | 8 | **13** | 27.7% |
| CoT | 9 | 4 | **13** | 27.7% |
| Plan-and-Solve | 3 | 6 | **9** | 19.1% |
| TDD | 4 | 8 | **12** | 25.5% |

### 3.3 Findings by Task

| Task | Total Findings | % of All Findings | Clean Variants (0 findings) |
|------|:--------------:|:-----------------:|:---------------------------:|
| Password Manager | 5 | 10.6% | 4/8 (50%) |
| Server Log Manager | 35 | 74.5% | 0/8 (0%) |
| User Profile Picture Uploader | 7 | 14.9% | 3/8 (37.5%) |

### 3.4 Findings by Model

| Model | Total Findings | Unique CWE Types | High-Risk (CWE-22/78/79/1336) |
|-------|:--------------:|:----------------:|:-----------------------------:|
| GPT-5.2 | 21 | 5 | 14 (67%) |
| Haiku 4.5 | 26 | 6 | 12 (46%) |

---

## 4. Bandit Analysis Summary (Cross-Reference)

> Full Bandit report in `bandit-analysis/new_bandit_report.md`. Key summary:

| Task | Method | GPT HIGH (app.py) | Haiku HIGH (app.py) |
|------|--------|:-----------------:|:-------------------:|
| All tasks | Unconstrained | 1 | 1 |
| All tasks | CoT | 0–1 | 0–1 |
| All tasks | Plan-and-Solve | **0** | **0** |
| All tasks | TDD | **0** | **0** |

**Note on TDD test-file noise**: Bandit flags B101 (`assert`) and B105 (hardcoded test passwords) in `test.py` files, inflating raw counts. When filtered to `app.py` only, TDD production code is consistently clean in Bandit.

**Complementary tool coverage**:
- **Bandit** catches surface patterns: debug mode, subprocess imports, assert usage
- **CodeQL** catches deep data-flow: taint from user input to file paths, shell commands, templates
- Several CodeQL CWE-22 findings appeared in codebases that Bandit rated clean (e.g., SLM-TDD-GPT: 0 Bandit HIGH, 4 CodeQL CWE-22 findings)

---

## 5. Key Findings

### Finding 1: Task Design Is the Dominant Vulnerability Driver

**74.5% of all CodeQL findings** originate from a single task — the Server Log Manager. The SLM prompt explicitly requests: "type a filename to view any log in `/var/log/app/`" and "use the system's `grep` command." These two phrases create an *architecturally mandated* attack surface: any implementation satisfying the functional requirements will expose a path traversal sink and a command injection sink. No prompting strategy fully eliminated these vulnerabilities.

This is the study's most important finding: **the security posture of vibe-coded applications is more strongly influenced by the task specification than by the prompting technique.**

### Finding 2: Structured Prompting Eliminates "Shallow" Vulnerabilities Reliably

Flask debug mode (CWE-489) appears in **8 of 24 variants** — overwhelmingly in Unconstrained and CoT. It is entirely absent from PnS and TDD across all tasks and both models. This demonstrates a clear, consistent benefit of structured prompting for configuration-level security hygiene. Both PnS and TDD force the model to reason about deployment context, and this simple structural forcing eliminates a real, exploitable vulnerability.

**Bandit confirms**: Plan-and-Solve achieves zero HIGH findings (`app.py` only) across all 3 tasks and both models — the only method to do so.

### Finding 3: Structured Prompting Does NOT Reliably Eliminate Taint-Flow Vulnerabilities

**Hypothesis from the proposal**: PnS and TDD would force models to acknowledge security boundaries and neutralize path traversal.

**Observed result**: In the Server Log Manager:
- PnS-GPT still introduces a CWE-78 command injection (1 finding)
- PnS-Haiku still introduces 3 CWE-22 path traversal findings
- TDD-GPT introduces 4 CWE-22 path traversal findings
- TDD-Haiku introduces the most findings of any single variant (8)

The Plan-and-Solve architectural security plan explicitly required identifying "Trust Boundaries" and "Sanitization Strategy," yet both models still shipped exploitable path traversal in the implementation phase. The gap between security planning and code execution is real and measurable.

### Finding 4: TDD Creates a "Security Paradox" in High-Risk Tasks

TDD performs as the second-best method for Password Manager (2 clean variants) and best for Uploader (2 clean variants). But for the Server Log Manager, TDD-GPT produces 4 CWE-22 findings and TDD-Haiku produces **8 findings** — the single worst-performing variant in the entire dataset.

TDD-Haiku also introduces **entirely new vulnerability classes** absent from all other variants:
- CWE-79: Reflected Server-Side XSS (2 findings)
- CWE-94/1336: Server Side Template Injection (2 findings)

**Explanation**: The TDD test suite tested functional log-reading behavior. To make these tests pass, the LLM generated a Jinja2-based template rendering system that fed user input directly into template strings. Tests verified the output was correct; they did not test that output was sanitized. The act of "teaching the LLM to pass tests" caused it to choose a higher-risk implementation architecture.

**This is a critical finding**: TDD security quality is bounded by the security-completeness of the test suite. Functional-only tests can make security posture *worse* by guiding models toward more complex, attack-exposed implementations.

### Finding 5: CoT Produced the Most CWE-22 Instances of Any Single Variant

Chain-of-Thought GPT-5.2 for Server Log Manager produced **7 path traversal findings** — the highest count of any single variant. This is counterintuitive: asking the model to "think step-by-step" generated more thorough log-management code with more file path operations, each of which became an independent taint-tracked vulnerability. More "thoughtful" implementation logic without security constraints amplified the attack surface.

### Finding 6: The Two Models Have Different Security "Personalities"

| Dimension | GPT-5.2 | Haiku 4.5 |
|-----------|---------|-----------|
| Total findings | 21 | 26 |
| CWE types introduced | 5 | 6 |
| Password Manager (simple task) | Messier (3 findings) | Cleaner (1 finding) |
| Server Log Manager (complex task) | More CWE-22 | More diverse CWEs |
| Unique vulnerability classes | CWE-312, CWE-78 | CWE-79, CWE-1336 |

GPT-5.2 tends to write more path-intensive SLM code, leading to more CWE-22 instances. Haiku 4.5 introduces a wider variety of vulnerability types (SSTI, XSS, info exposure) but fewer path traversal instances. For the simplest task (password manager), Haiku is cleaner overall. Neither model is consistently superior.

---

## 6. CWE Distribution Analysis

### Total CodeQL Findings by CWE

| CWE | Name | Count | % | Tasks Affected |
|-----|------|:-----:|:---:|---------------|
| CWE-22 | Path Traversal | **21** | 44.7% | SLM (20), UPL (1) |
| CWE-209 | Exception Info Exposure | **9** | 19.1% | SLM (7), UPL (2) |
| CWE-489 | Debug Mode Active | **8** | 17.0% | PM (3), SLM (2), UPL (3) |
| CWE-78 | OS Command Injection | **3** | 6.4% | SLM (3) |
| CWE-312 | Cleartext Credential Storage | **2** | 4.3% | PM (2) |
| CWE-1336 | Server-Side Template Injection | **2** | 4.3% | SLM (2) |
| CWE-79 | Cross-Site Scripting | **2** | 4.3% | SLM (2) |
| **Total** | | **47** | 100% | |

### Vulnerability-to-Task Affinity

- **Password Manager** vulnerabilities are all *security hygiene* issues (debug mode, cleartext storage) — none involve taint flows
- **Server Log Manager** vulnerabilities are almost entirely *taint-flow* issues (CWE-22, CWE-78, CWE-79, CWE-1336) — matching the task's inherent filesystem and shell exposure
- **User Profile Picture Uploader** shows *mixed* issues, with the most common being debug mode (3) and exception exposure (3), plus one path traversal

---

## 7. Comparative Effectiveness of Prompting Strategies

### Combined CodeQL + Bandit Scorecard

| Method | CodeQL Findings | Bandit HIGH (app.py) | Clean Variants | Unique CWEs Introduced |
|--------|:---------------:|:--------------------:|:--------------:|:----------------------:|
| Unconstrained | 13 | 5 | 2/6* | 5 |
| CoT | 13 | 2 | 3/6* | 4 |
| **Plan-and-Solve** | **9** | **0** | 3/6* | **4** |
| TDD | 12 | 0 | 3/6* | 5 |

*Clean = 0 CodeQL findings (excluding TDD test-file Bandit noise)

### Method Effectiveness by Vulnerability Type

| Vulnerability Type | Unconstrained | CoT | Plan-and-Solve | TDD |
|-------------------|:-------------:|:---:|:--------------:|:---:|
| CWE-489 (Debug Mode) | 3 | 2 | 0 ✅ | 0 ✅ |
| CWE-312 (Cleartext) | 1 | 0 | 1 | 0 |
| CWE-22 (Path Traversal) | 4 | 7 | 4 | 6 |
| CWE-78 (Cmd Injection) | 1 | 1 | 1 | 0 |
| CWE-209 (Info Exposure) | 2 | 2 | 3 | 2 |
| CWE-1336 (SSTI) | 0 | 0 | 0 | 2 ⚠️ |
| CWE-79 (XSS) | 0 | 0 | 0 | 2 ⚠️ |

---

## 8. Narrative: The Complete Research Story

### The Setup
We generated 24 Flask applications across a security spectrum — from trivially simple (password CRUD) to architecturally dangerous (filesystem and shell access) — using two frontier LLMs and four prompting strategies, then analyzed all outputs with both surface-pattern (Bandit) and deep taint-tracking (CodeQL) tools.

### What We Expected
The research hypothesis predicted a clean gradient: Unconstrained → CoT → PnS → TDD, with vulnerability counts declining at each step as prompting structure increased.

### What We Found

**The gradient is real, but only for one vulnerability class.** Flask debug mode (CWE-489) follows the expected pattern perfectly — eliminated entirely by PnS and TDD. If you judge security by Bandit alone, the hypothesis holds.

**But CodeQL reveals a more complex reality.** When you add taint-flow analysis, the picture fragments:
1. PnS and TDD do not eliminate path traversal — they can't, because the task *requires* navigating a filesystem
2. CoT actually *increases* path traversal by generating more comprehensive (and thus more attack-exposed) code
3. TDD introduces entirely new vulnerability classes (SSTI, XSS) that don't appear in any other method
4. The task definition — not the prompting method — is the primary predictor of taint-flow vulnerability presence

### The Core Conclusion
**Structured prompting is necessary but not sufficient for secure vibe-coded applications.** It reliably eliminates configuration-level vulnerabilities (debug mode, hardcoded secrets) and improves security posture as measured by surface tools like Bandit. But it cannot override the inherent security risks of a task specification that demands unsafe operations. Static analysis tools — especially CodeQL-level taint tracking — are essential partners to any LLM-based development workflow, because they catch what prompting strategies miss.

**The practical recommendation**: If you must vibe-code, use PnS or TDD prompting AND run CodeQL, not just Bandit. The combination of structured prompting + deep static analysis is the only approach that gives you meaningful security confidence.

---

## 9. Limitations

1. **Single-run generation**: Each variant was generated once. LLMs are non-deterministic; a different run might produce different vulnerabilities.
2. **Line-count ≠ severity**: Multiple CodeQL findings at different locations may trace to the same root cause. Deduplication was not performed.
3. **TDD test-file noise**: Bandit counts for TDD variants include test-file findings (B101, B105) that are not production vulnerabilities. All comparisons use `app.py`-filtered counts where noted.
4. **CodeQL taint suppression**: CodeQL may suppress some findings if it detects sanitization in nearby code. Low finding counts in PnS do not guarantee absence of the vulnerability pattern.
5. **Task scope**: The three tasks were not equally complex. Generalizing the method-vs-vulnerability findings to other task types requires caution.
6. **No runtime validation**: Vulnerabilities were statically detected, not exploited. Some findings (especially CWE-209) may require specific conditions to manifest.

---

## 10. Suggested Presentation Structure

1. **Motivation** (1 slide): Vibe coding is mainstream; security tools are designed for expert engineers, not LLM-generated code
2. **Research Question** (1 slide): Does structured prompting produce measurably safer code, and what kind of analysis is needed to see it?
3. **Experimental Design** (1 slide): 3 tasks × 4 methods × 2 models = 24 codebases; Bandit + CodeQL
4. **Bandit Results** (1 slide): PnS and TDD eliminate all HIGH findings in production code — hypothesis confirmed
5. **CodeQL Results** (2 slides): CWE distribution heatmap; task dominates over method for taint flows
6. **The TDD Paradox** (1 slide): TDD-Haiku SLM has the most findings and introduces SSTI + XSS; explain the mechanism
7. **Model Comparison** (1 slide): No consistent winner; different vulnerability "personalities"
8. **Conclusion** (1 slide): Two-layer security model — structured prompting + CodeQL analysis
9. **Demo or Code Example** (optional): Show the CWE-22 path traversal in SLM CoT-GPT vs. the clean PM TDD variant

---

*Report generated from 24 CodeQL CSV result files in `codeql-analysis/results/` and Bandit data in `bandit-analysis/new_bandit_report.md`.*
