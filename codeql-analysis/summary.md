# CodeQL Security Analysis Summary

## Analysis Overview
- **Tool**: CodeQL CLI v3.12.11
- **Language**: Python
- **Queries**: Python Security Queries v1.8.1
- **Target Applications**: password_manager, server_log_manager, user_profile_picture_uploader
- **Methods Analyzed**: vibe, cot, pns, tdd

## CWE-22 Path Traversal Vulnerabilities

### By Application and Method

| Application | Vibe | CoT | P&S | TDD | Total |
|-------------|------|-----|-----|-----|-------|
| password_manager | 0 | 0 | 0 | 0 | 0 |
| server_log_manager | 4 | 7 | 3 | 6 | 20 |
| user_profile_picture_uploader | 0 | 0 | 1 | 0 | 1 |
| **Total** | **4** | **7** | **4** | **6** | **21** |

### Key Findings
- **Primary Vulnerability**: "Uncontrolled data used in path expression"
- **Most Affected Application**: server_log_manager (20/21 total CWE-22 issues)
- **Method with Highest Average**: CoT (2.3 avg CWE-22 per app)
- **Method with Lowest Average**: Vibe/P&S (1.3 avg CWE-22 per app)

## All Detected Vulnerabilities

| Vulnerability Type | Count |
|-------------------|-------|
| Uncontrolled data used in path expression | 21 |
| Information exposure through an exception | 9 |
| Flask app is run in debug mode | 8 |
| Uncontrolled command line | 3 |
| Clear-text storage of sensitive information | 2 |
| Server Side Template Injection | 2 |
| Reflected server-side cross-site scripting | 2 |

## Analysis Details
- **Total CodeQL Databases Created**: 24
- **Total Result Files Generated**: 24
- **Python Files Analyzed**: ~2 per variant (app.py, test.py)
- **Analysis Date**: May 4, 2026

## Notes
- CodeQL successfully detected CWE-22 vulnerabilities that Bandit missed
- Path traversal issues were concentrated in server_log_manager application
- Other applications (password_manager, uploader) showed minimal path-related vulnerabilities</content>
<parameter name="filePath">/Users/dl/spring2026/spa/vibe-coding-security-analysis/codeql-analysis/summary.md