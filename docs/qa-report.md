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
| 11 | Portfolio metric reconciliation | **PASS** | Ten prominent metrics reconcile from clean data through portfolio_metrics.json to the README snapshot. |
| 12 | JSON syntax | **PASS** | Parsed 189 JSON files with UTF-8 decoding. |
| 13 | Microsoft schema declarations | **PASS** | All PBIP/PBIR semantic-model JSON artifacts declare current Microsoft Fabric schema URLs. |
| 14 | PBIP artifact references | **PASS** | PBIP resolves to the report artifact and PBIR resolves to the sibling semantic model by path. |
| 15 | Current report schema and theme package | **PASS** | Report uses Microsoft report schema 3.2.0 with a matching RegisteredResources custom-theme package. |
| 16 | Enhanced PBIR structure | **PASS** | 8 ordered pages and 168 structurally complete visual containers. |
| 17 | TMDL static validation | **PASS** | Measures=79; relationships=13; multi-line DAX fences balanced. |
| 18 | Marked date-table semantics | **PASS** | DimDate is categorized as Time; the related Date column is the key and the hidden integer surrogate is not the date key. |
| 19 | Semantic display ordering | **PASS** | Month, status, severity and risk labels use governed numeric sort columns. |
| 20 | Relationship direction | **PASS** | No bidirectional filter declaration; exactly two role-playing date relationships are inactive. |
| 21 | DAX safety and terminology | **PASS** | Explicit measures use DIVIDE, governed open-status logic and synthetic/human-review terminology; Desktop parsing remains a final host check. |
| 22 | SQL analytical coverage | **PASS** | Six SQL modules include CTEs, CASE, views and window functions. |
| 23 | Python syntax | **PASS** | All project Python scripts compile successfully. |
| 24 | CI workflow contract | **PASS** | Push, pull-request and manual triggers run the documented Python install → generate → validate → clean → build → QA sequence with read-only contents permission. |
| 25 | Internal links | **PASS** | Zero broken internal Markdown links. |
| 26 | Generated Markdown structure | **PASS** | Generated documentation tables begin at the left margin and render as Markdown rather than code blocks. |
| 27 | External link hygiene | **PASS** | All 6 external Markdown links use HTTPS and approved first-party documentation or repository hosts. |
| 28 | Privacy and neutral branding | **PASS** | No named employer, email address, local user path or credential pattern appears in project artifacts; all claim, policy, handler and supplier data is synthetic. |
| 29 | Preview asset integrity | **PASS** | Eight 1600×900 PNG assets are explicitly labelled DESIGN MOCKUP; no screenshot claim is made. |
| 30 | Repository credibility | **PASS** | No lorem ipsum, coming-soon copy or placeholder-junk files. |
| 31 | Desktop evidence boundary | **PASS** | Runtime results remain MANUAL REVIEW and no Power BI screenshot asset is claimed or present without Desktop evidence. |
| 32 | Recruiter evidence pack | **PASS** | Walkthrough timing, eight page captions, technical interview answers and README links are complete. |
| 33 | README recruiter presentation | **PASS** | The opening evidence line, executive summary, concise case study and core recruiter sections are present. |

## Outcome

**33 of 33 checks passed.**

Microsoft schema URLs are declared on every relevant PBIP/PBIR JSON artifact and structural validation is automated. Full JSON Schema evaluation and runtime TMDL/DAX/visual rendering still require a current Power BI Desktop host; that host was not installed in the build environment. No PBIX or screenshot was fabricated.
