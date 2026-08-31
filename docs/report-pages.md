# Report page specification

The enhanced PBIR report contains **8 pages and 168 visual containers**. Standard Power BI page tabs provide navigation; each page also has a consistent navigation header, four primary slicers and a synthetic-data disclosure.

| # | Page | Audience | Analytical views |
|---:|---|---|---|
| 1 | Executive Claims Overview | Claims Executive / COO | Claims volume trend, Total incurred trend, Severity trend, Claims by product, Claims by region, Claim status |
| 2 | Claims Operations | Claims Operations Leadership | Ageing distribution, Backlog trend, Claims by lifecycle stage, Settlement time by complexity, SLA trend, Open claims by reason |
| 3 | Risk & Review Intelligence | Risk / SIU Manager | Risk-band distribution, Risk by claim type, Risk by region, Risk vs reporting delay, Risk by severity, Non-target review exposure |
| 4 | Financial Performance | Finance Executive | Incurred movement by claim type, Cost trend, Product exposure, Regional exposure, Severity mix, Reserve concentration |
| 5 | Regional Intelligence | Regional Claims Leadership | South African province exposure, Claims volume by province, Average severity by province, Settlement days by province, SLA compliance by province, High-risk exposure by province |
| 6 | Handler Performance | Claims Team Leadership | Workload by handler, Service by handler, Quality by handler, Complexity-adjusted exposure, Workload vs service, Balanced scorecard |
| 7 | Root Cause Analysis | BI and Claims Leadership | Why did the selected metric change?, Product → claim type, Region contribution, Severity-band contribution, Channel contribution, Selected metric trend |
| 8 | Data Quality | BI Manager / Data Steward | Issues by category, Issues over ingestion batches, Issues by severity, Validation outcomes, Issue concentration by claim stage, Issue counts by region |

## UX implementation status

| Feature | Status |
|---|---|
| Enhanced PBIR page definitions | Source-configured |
| Standard page-tab navigation and executive nav header | Source-configured |
| Date, product, region and risk slicers | Source-configured |
| Investigation-capacity what-if table (5/10/15/20) | TMDL-configured |
| Analysis metric field-parameter table | TMDL-configured |
| Dynamic executive attention measures | DAX-configured |
| RLS roles | TMDL-configured, conceptual only |
| Enhanced tooltips setting | Enabled in report metadata |
| Theme, accessible high-contrast palette | Delivered as importable JSON |
| Bookmarks, reset action, synced slicers, drill-through target, phone layouts | Desktop verification/configuration required |

Risk scores prioritize review. They do not automatically determine fraud. Handler views are for balanced workload management, not employee performance management.

Recruiter-facing page purposes and captions are documented in [report-page-guide.md](report-page-guide.md).
