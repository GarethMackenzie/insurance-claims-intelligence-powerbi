# QA report

Run with `python scripts/qa_project.py` using Python 3.12.13.

| # | Check | Result | Evidence |
|---:|---|---|---|
| 1 | Required file structure | **PASS** | All required project, documentation, theme and governance files exist. |
| 2 | Reproducible build | **PASS** | All four build scripts executed; raw, issue-log and fact SHA-256 hashes are stable. |
| 3 | Dataset row counts | **PASS** | Raw=75,150; clean FactClaims=75,000. |
| 4 | Unique clean claim grain | **PASS** | FactClaims is one row per 75,000 unique synthetic Claim_ID values. |
| 5 | Controlled issue rate | **PASS** | 2,150 issue events = 2.87% of canonical claims. |
| 6 | Issue detection | **PASS** | Seeded=2,150; detected=2,150; detection=100%. |
| 7 | Positive amounts | **PASS** | All clean Claim_Amount values are positive. |
| 8 | Financial reconciliation | **PASS** | Maximum /incurred - paid - reserve/ = 0.0000. |
| 9 | Lifecycle dates | **PASS** | Report dates follow loss dates and no clean settlement date is after 2026-08-31. |
| 10 | Dimension key integrity | **PASS** | No orphan surrogate keys across nine categorical dimensions. |
| 11 | JSON syntax | **PASS** | Parsed 189 JSON files with UTF-8 decoding. |
| 12 | Microsoft schema declarations | **PASS** | All PBIP/PBIR semantic-model JSON artifacts declare current Microsoft Fabric schema URLs. |
| 13 | Current report schema and theme package | **PASS** | Report uses Microsoft report schema 3.2.0 with a matching RegisteredResources custom-theme package. |
| 14 | Enhanced PBIR structure | **PASS** | 8 ordered pages and 168 structurally complete visual containers. |
| 15 | TMDL static validation | **PASS** | Measures=79; relationships=13; multi-line DAX fences balanced. |
| 16 | Relationship direction | **PASS** | No bidirectional filter declaration; two role-playing date relationships are explicitly inactive. |
| 17 | DAX safety patterns | **PASS** | Explicit measure table uses DIVIDE and documented formats; Desktop parsing remains a final host check. |
| 18 | SQL analytical coverage | **PASS** | Six SQL modules include CTEs, CASE, views and window functions. |
| 19 | Python syntax | **PASS** | All project Python scripts compile successfully. |
| 20 | Internal links | **PASS** | Zero broken internal Markdown links. |
| 21 | Privacy and neutral branding | **PASS** | No named employer branding appears in project text; all claim, policy, handler and supplier data is synthetic. |
| 22 | Preview asset integrity | **PASS** | Eight 1600×900 PNG assets are explicitly labelled DESIGN MOCKUP; no screenshot claim is made. |
| 23 | Repository credibility | **PASS** | No lorem ipsum, coming-soon copy or placeholder-junk files. |

## Outcome

**23 of 23 checks passed.**

Microsoft schema URLs are declared on every relevant PBIP/PBIR JSON artifact and structural validation is automated. Full JSON Schema evaluation and runtime TMDL/DAX/visual rendering still require a current Power BI Desktop host; that host was not installed in the build environment. No PBIX or screenshot was fabricated.
