# Insurance Claims Intelligence

[![Project QA](https://github.com/GarethMackenzie/insurance-claims-intelligence-powerbi/actions/workflows/ci.yml/badge.svg)](https://github.com/GarethMackenzie/insurance-claims-intelligence-powerbi/actions/workflows/ci.yml)

**Executive Claims Performance, Fraud Risk & Operational Analytics Command Center**

An end-to-end Power BI insurance analytics portfolio project combining dimensional modelling, Power Query, DAX, operational analytics, financial exposure analysis, risk-based review prioritization and executive reporting.

> **Portfolio demonstration using synthetic data only.** No customer, policyholder, claim, or employer-confidential information is used. All findings are synthetic portfolio findings, not workplace achievements.

## Business problem

Claims leaders need a governed view of cost, severity, lifecycle delay, SLA, backlog, reserve exposure, regional concentration and limited fraud-review capacity. This solution is designed around management questions: what changed, where pressure is building, why it matters, and what to investigate next.

## What I built

- A deterministic Python generator for **75,000 synthetic claims** from 2024-01-01 to 2026-08-31.
- A controlled raw-data challenge with **2,150 quality issue events** and a complete correction audit.
- A clean star schema with `FactClaims`, ten conformed dimensions and 13 relationships.
- A source-control-friendly PBIP project using enhanced PBIR report definitions and TMDL semantic-model files.
- A dedicated DAX measure layer with **79 explicit measures**, time intelligence, dynamic exceptions, balanced handler analytics and a review-capacity simulator.
- Eight executive report pages, 168 visual containers, ANSI-oriented analytical SQL, reusable M and detailed documentation.

## Why it matters

The project demonstrates more than chart construction: reproducibility, data-quality governance, dimensional design, insurance operations, financial exposure, responsible risk terminology, human-in-the-loop prioritization and executive analytical storytelling.

## Portfolio snapshot

| Metric | Synthetic result |
|---|---:|
| Claims | 75,000 |
| Open claims | 9,331 |
| Total incurred | R9.05bn |
| Outstanding reserve | R1.84bn |
| Average severity | R143,507 |
| Median settlement days | 39 |
| SLA compliance | 61.4% |
| High/Critical risk share | 12.4% |
| Data quality detection | 2,150 / 2,150 (100%) |

## Technology

`Power BI Project (PBIP)` · `Enhanced PBIR` · `TMDL` · `DAX` · `Power Query M` · `Python` · `pandas` · `NumPy` · `SQL` · `Git/GitHub`

## Architecture

![Insurance Claims Intelligence solution architecture](assets/architecture.svg)

See [architecture](docs/architecture.md), [data model](docs/data-model.md), [methodology](docs/methodology.md), and the complete [data dictionary](docs/data-dictionary.md) (110 fields).

## Dashboard design mockups

These images are **design mockups, not Power BI screenshots**. The editable visual definitions are in [`InsuranceClaimsIntelligence.Report`](InsuranceClaimsIntelligence.Report/definition/pages/).

| Executive overview | Claims operations |
|---|---|
| ![Executive overview design mockup](assets/executive-overview.png) | ![Claims operations design mockup](assets/claims-operations.png) |
| Fraud & risk | Financial performance |
| ![Fraud and risk design mockup](assets/fraud-risk.png) | ![Financial performance design mockup](assets/financial-performance.png) |
| Regional intelligence | Handler performance |
| ![Regional intelligence design mockup](assets/regional-intelligence.png) | ![Handler performance design mockup](assets/handler-performance.png) |
| Root-cause analysis | Data quality |
| ![Root cause design mockup](assets/root-cause-analysis.png) | ![Data quality design mockup](assets/data-quality.png) |

Page scope and feature status are documented in [report-pages.md](docs/report-pages.md).

## Key synthetic findings

1. **Fire leads incurred exposure** — It contributes R1,653,712,314, or 18.3%, of total incurred.
2. **Free State has the strongest comparable severity increase** — Synthetic average severity is +15.9% versus January–August 2025.
3. **Aged open claims concentrate reserve exposure** — They represent 75.0% of open claims and 79.9% of open-claim reserves.
4. **Assessment is the weakest open-stage SLA segment** — SLA compliance is 39.7% for the segment.
5. **High-risk concentration is greatest in KwaZulu-Natal** — The concentration is 15.8% of claims in the province.
6. **Agricultural claims have the longer median settlement cycle** — Agricultural records 67 days versus 32 days for the other product.

Read the evidence, implications and cautious action framing in [executive-insights.md](docs/executive-insights.md).

## Data model

![Insurance claims star schema](assets/data-model.svg)

Dimensions filter `FactClaims` one-to-many in a single direction. Loss date is the active date path; report and settlement date are inactive role-playing relationships. Disconnected capacity and analysis-metric tables support what-if and parameterized analysis.

## DAX, Power Query and SQL

- [DAX measure catalogue](dax/measures.md) documents every explicit measure and format.
- [Power Query design](docs/power-query.md) explains staging, reusable functions, type enforcement, duplicate detection and validation.
- [`sql/`](sql/) contains dimensional DDL, data-quality checks, performance views, risk-capacity logic and financial analysis using CTEs and window functions.

## Data quality

The raw layer contains 75,150 rows and 2,150 controlled issue events across missing values, negative amounts, category variants, invalid dates, whitespace, invalid claim types and duplicates. The validator detected all events, and the clean fact reconciles to 75,000 unique claims. See [data-quality.md](docs/data-quality.md).

## How to run

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/generate_synthetic_claims.py
python scripts/validate_data.py
python scripts/build_clean_dataset.py
python scripts/build_project.py
python scripts/qa_project.py
```

Then open [`InsuranceClaimsIntelligence.pbip`](InsuranceClaimsIntelligence.pbip) in a current Power BI Desktop release. If the clone location changed, update the `pProjectRoot` parameter before refresh. Full instructions are in [power-bi-setup.md](docs/power-bi-setup.md).

## Repository map

```text
InsuranceClaimsIntelligence.pbip
InsuranceClaimsIntelligence.Report/       enhanced PBIR report source
InsuranceClaimsIntelligence.SemanticModel/ TMDL semantic model source
data/raw/ and data/clean/                  reproducible synthetic extracts
scripts/                                   generation, validation, clean build and QA
powerquery/                                reusable M and staging examples
dax/                                       measure catalogue and field parameter
sql/                                       six analytical SQL modules
docs/                                      architecture, method, governance and setup
assets/                                    diagrams and labelled design mockups
theme/                                     Power BI theme JSON
```

## Limitations and responsible use

This is synthetic data with a simplified lifecycle and reserve methodology. It is not production-validated, actuarial, causal or representative of real customer behaviour. The risk score is not a fraud determination. RLS is conceptual. Handler analytics are for workload-management demonstration, not employee performance management. Read all [limitations](docs/limitations.md) and [RLS notes](docs/row-level-security.md).

## Privacy

The project contains no real customer, policyholder, claim, employer, user or credential data. Handler and supplier labels are neutral synthetic identifiers. No employer branding appears in the report.

## Quality assurance

The build validates reproducibility, data invariants, issue detection, JSON parsing and schema declarations, TMDL structure, relationship direction, DAX inventory, SQL content, internal links, privacy terms and preview labels. Results are in [qa-report.md](docs/qa-report.md).

## Author

**Gareth Andrew Mackenzie**<br>
Johannesburg, South Africa

Licensed under the [MIT License](LICENSE).
