# Vibe Coding Security Analysis

**Does structured prompting make LLM-generated code safer?**  
A static analysis study of 24 AI-generated Flask applications across four prompting strategies and two frontier models.

> Jaehyeon Kim · Daewoong Lim · Sihyun Kim · Yongje Jeon  
> SPA Final Project — Spring 2026

---

## Overview

"Vibe coding" — generating production code from minimal, conversational prompts — is now mainstream. But how safe is the code it produces? And does asking an LLM to *think about security* actually help?

We generated **24 Flask web applications** by crossing:
- **3 tasks**: Password Manager, Server Log Manager, User Profile Picture Uploader
- **4 prompting methods**: Unconstrained, Chain-of-Thought, Plan-and-Solve, Test-Driven Development
- **2 models**: GPT-5.2 (OpenAI) and Claude Haiku 4.5 (Anthropic)

Each codebase was analyzed with two complementary static analysis tools — **Bandit** (AST pattern matching) and **CodeQL** (inter-procedural taint tracking) — to detect vulnerabilities across seven CWE categories.

---

## Key Findings

### 1. Task design matters more than prompting method
74.5% of all CodeQL findings came from a single task — the Server Log Manager — because its prompt explicitly required filesystem navigation and shell command execution. No prompting strategy fully eliminated these taint-flow vulnerabilities. **The task specification is a stronger predictor of vulnerability presence than the prompting technique.**

### 2. Structured prompting eliminates shallow vulnerabilities reliably
Flask debug mode (CWE-489) is present in Unconstrained and CoT variants but **completely absent** from all Plan-and-Solve and TDD outputs. Plan-and-Solve is the only method with zero Bandit HIGH-severity findings across all tasks and both models.

### 3. Structured prompting does NOT reliably eliminate deep taint flows
Plan-and-Solve still ships exploitable CWE-22 path traversal in the Server Log Manager despite requiring an explicit architectural security plan. The gap between security *planning* and *implementation* is real and measurable.

### 4. TDD paradox: functional tests can make security worse
TDD + Haiku 4.5 on the Server Log Manager is the single worst-performing variant (8 CodeQL findings), introducing **Server-Side Template Injection (CWE-94/1336)** and **Reflected XSS (CWE-79)** — vulnerability classes absent from every other variant. Tests that verify functional correctness guided the LLM toward a riskier implementation architecture.

### 5. No model wins consistently
GPT-5.2 introduces more CWE-22 path traversal; Haiku 4.5 introduces more diverse vulnerability classes (SSTI, XSS, exception exposure). For simple tasks, Haiku is cleaner; for complex tasks, GPT is.

---

## Vulnerability Summary (CodeQL, 47 total findings)

| CWE | Vulnerability | Count | Primary Source |
|-----|--------------|:-----:|----------------|
| CWE-22 | Path Traversal | 21 | Server Log Manager |
| CWE-209 | Exception Info Exposure | 9 | Server Log Manager, Uploader |
| CWE-489 | Flask Debug Mode Active | 8 | All tasks (Unconstrained/CoT only) |
| CWE-78 | OS Command Injection | 3 | Server Log Manager |
| CWE-312 | Cleartext Credential Storage | 2 | Password Manager |
| CWE-1336 | Server-Side Template Injection | 2 | Server Log Manager (TDD only) |
| CWE-79 | Cross-Site Scripting | 2 | Server Log Manager (TDD only) |

---

## Repository Structure

```
.
├── programs/                        # All 24 generated codebases
│   ├── password_manager/
│   │   ├── 1-unconstrained-gpt5.2/
│   │   ├── 1-unconstrained-haiku4.5/
│   │   ├── 2-CoT-{gpt5.2,haiku4.5}/
│   │   ├── 3-PnS-{gpt5.2,haiku4.5}/
│   │   └── 4-TDD-{gpt5.2,haiku4.5}/
│   ├── server_log_manager/          # (same structure)
│   └── user_profile_picture_uploader/
│
├── prompts/                         # Prompts used for each task & method
│   ├── password_manager.md
│   ├── server_log_manager.md
│   └── user_profile_picutre_uploader.md
│
├── codeql-analysis/
│   ├── results/                     # 24 CodeQL CSV result files
│   └── summary.md
│
├── bandit-analysis/
│   ├── new_results/                 # 24 Bandit JSON result files
│   ├── new_bandit_report.md         # Full Bandit analysis report
│   └── summary2.csv
│
├── analysis/
│   └── security_analysis_report.md  # Full cross-tool analysis & findings
│
├── bib/                             # Reference papers
└── SPA Project Proposal Document.md
```

---

## Prompting Methods

| Method | Description |
|--------|-------------|
| **Unconstrained** | Minimal, conversational prompt — functional requirements only, no security guidance |
| **Chain-of-Thought (CoT)** | Added instruction to think step-by-step before writing code |
| **Plan-and-Solve (PnS)** | Required a formal security planning phase (trust boundaries, threat modeling, sanitization strategy) before any code |
| **TDD** | Provided a test suite; generated code had to pass all tests via pytest |

---

## Analysis Tools

| Tool | Type | What It Catches |
|------|------|----------------|
| **Bandit** | AST pattern matching | Debug mode, subprocess imports, hardcoded credentials, assert usage |
| **CodeQL** v3.12.11 | Inter-procedural taint tracking | Path traversal, command injection, SSTI, XSS, exception leakage, cleartext storage |

The two tools are complementary: several variants scored zero Bandit HIGH findings but still had critical CodeQL taint-flow vulnerabilities (e.g., SLM-TDD-GPT: clean in Bandit, 4 CWE-22 findings in CodeQL).

---

## Full Analysis

See [analysis/security_analysis_report.md](analysis/security_analysis_report.md) for the complete findings including all data tables, CWE taxonomy, per-variant breakdown, and the research narrative.

---

## References

1. <!-- asleep_at_the_keyboard.pdf --> ‌Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., & Karri, R. (2021). Asleep at the Keyboard? Assessing the Security of GitHub Copilot’s Code Contributions. https://arxiv.org/abs/2108.09293 

2. <!-- do_users_write_more_insecure_code.pdf --> Perry, N., Srivastava, M., Kumar, D., & Boneh, D. (2022). Do Users Write More Insecure Code with AI Assistants? CCS '23: Proceedings of the 2023 ACM SIGSAC Conference on Computer and Communications Security, November 2023, Pages 2785-2799. https://arxiv.org/abs/2211.03622

3. <!-- empirical_security_evaluation.pdf --> Elsayed, M., Fulton, K., & Yang, J. (2026). An Empirical Security Evaluation of LLM-Generated Cryptographic Rust Code. ArXiv.org. https://arxiv.org/abs/2604.27001

4. <!-- is_vibe_coding_safe.pdf --> Zhao, S., Wang, D., Zhang, K., Luo, J., Li, Z., & Li, L. (2025). Is Vibe Coding Safe? Benchmarking Vulnerability of Agent-Generated Code in Real-World Tasks. ArXiv.org. https://arxiv.org/abs/2512.03262v2
