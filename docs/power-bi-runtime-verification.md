# Power BI runtime verification

## Current status

| Field | Value |
|---|---|
| Repository-side inspection date | 2026-08-31 |
| Power BI Desktop version | Not available in the current execution environment |
| Desktop verification date | Not completed |
| Tester | Not assigned |
| Overall runtime result | **MANUAL REVIEW** |
| Refresh result | **MANUAL REVIEW** |
| Genuine Desktop screenshots | None |

Power BI Desktop was not installed or available to the current user during this repository pass. No report refresh, DAX execution, visual render, interaction, PBIX or screenshot result is claimed here.

Automated evidence remains available in [`qa-report.md`](qa-report.md). The exact Desktop procedure is in [`desktop-verification-checklist.md`](desktop-verification-checklist.md).

## Core runtime tests

Update this table only while working in Power BI Desktop. Do not infer PASS from source structure.

| Test | Result | Evidence | Notes |
|---|---|---|---|
| PBIP opens without corruption | MANUAL REVIEW | — | Not exercised in this environment |
| Semantic model loads | MANUAL REVIEW | — | Not exercised in this environment |
| Report definition loads | MANUAL REVIEW | — | Not exercised in this environment |
| Custom theme applies | MANUAL REVIEW | — | Theme source exists; render not exercised |
| `pProjectRoot` resolves | MANUAL REVIEW | — | Must be set to the clone path |
| Data refresh completes | MANUAL REVIEW | — | Not exercised in this environment |
| All model tables load | MANUAL REVIEW | — | Structural presence only |
| Relationships validate | MANUAL REVIEW | — | Static relationship checks pass |
| DAX measures compile | MANUAL REVIEW | — | Static inventory checks pass |
| No broken visual state | MANUAL REVIEW | — | PBIR structure passes; render not exercised |
| Eight report pages render | MANUAL REVIEW | — | Eight source pages exist |
| Slicers and cross-filtering work | MANUAL REVIEW | — | Not exercised in this environment |
| Field parameter works | MANUAL REVIEW | — | Source-configured only |
| Review-capacity parameter works | MANUAL REVIEW | — | Source-configured only |
| Drill-through works | MANUAL REVIEW | — | Requires Desktop verification/configuration |
| Tooltips work | MANUAL REVIEW | — | Enhanced tooltips enabled; behavior not exercised |
| Bookmarks and reset actions work | MANUAL REVIEW | — | Requires Desktop verification/configuration |
| Navigation works | MANUAL REVIEW | — | Not exercised in this environment |
| RLS example roles work | MANUAL REVIEW | — | Role source exists; effective behavior not exercised |
| Phone layouts are acceptable | MANUAL REVIEW | — | Requires Desktop inspection/configuration |

## Page-level runtime evidence

| # | Page | Result | Screenshot | Issue/retest notes |
|---:|---|---|---|---|
| 1 | Executive Claims Overview | MANUAL REVIEW | — | — |
| 2 | Claims Operations | MANUAL REVIEW | — | — |
| 3 | Risk & Review Intelligence | MANUAL REVIEW | — | — |
| 4 | Financial Performance | MANUAL REVIEW | — | — |
| 5 | Regional Intelligence | MANUAL REVIEW | — | — |
| 6 | Handler Performance | MANUAL REVIEW | — | — |
| 7 | Root Cause Analysis | MANUAL REVIEW | — | — |
| 8 | Data Quality | MANUAL REVIEW | — | — |

## Interaction evidence

| Interaction | Result | Evidence | Notes |
|---|---|---|---|
| Date filters | MANUAL REVIEW | — | Full period, year, month and range required |
| Product filters | MANUAL REVIEW | — | Motor and Agricultural required |
| Regional filters | MANUAL REVIEW | — | Test multiple provinces |
| Claim-type filters | MANUAL REVIEW | — | Test common and low-volume categories |
| Risk filters | MANUAL REVIEW | — | Test all bands |
| Status filters | MANUAL REVIEW | — | Test open and settled contexts |
| Field parameter | MANUAL REVIEW | — | Test all configured metrics |
| Capacity what-if parameter | MANUAL REVIEW | — | Test 5%, 10%, 15% and 20% |
| Drill-through | MANUAL REVIEW | — | Confirm destination context |
| Tooltips | MANUAL REVIEW | — | Confirm filter context |
| Bookmarks | MANUAL REVIEW | — | Record absent/implemented states |
| Reset filters | MANUAL REVIEW | — | Confirm default state |
| Navigation | MANUAL REVIEW | — | Test every destination |
| RLS demonstration | MANUAL REVIEW | — | Test both example roles |

## Completion rule

The README may state that Desktop verification succeeded only when this record contains the actual Desktop version, verification date, evidence links and completed results for refresh, all eight pages and core interactions.
