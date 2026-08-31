# Technical interview guide

## Why PBIP instead of only PBIX?

PBIP exposes report and semantic-model definitions as source-controlled text. That makes reviews, diffs, automated checks and team workflows possible in a way that a single opaque PBIX cannot provide. A PBIX can still be created after genuine Desktop validation if a binary distribution is needed.

## Why TMDL?

TMDL makes tables, columns, measures, relationships, roles, formats and partitions inspectable. It supports disciplined semantic-model review and allows QA to verify important structural conventions without claiming to replace Desktop execution.

## Why a star schema?

The fact table has one row per claim, while conformed dimensions provide governed product, region, status, risk and other business categories. This reduces repeated attributes, makes filter behavior predictable and supports reusable measures.

## Why single-direction relationships?

Dimensions should filter the fact table in a controlled direction. Avoiding bidirectional filters reduces ambiguity and makes filter propagation easier to reason about and test.

## Why inactive role-playing date relationships?

Loss date is the primary analytical path. Report and settlement dates are valid alternative roles, but making all three active would create ambiguity. Measures that require another date role should activate it explicitly with `USERELATIONSHIP`.

## Why explicit measures?

Explicit measures centralize business definitions, formatting and filter behavior. They are more reviewable and reusable than implicit visual aggregations, so the model discourages implicit measures.

## Why 79 measures?

The count is an outcome of the analytical scope, not a target. Measures cover volume, finance, severity, service, backlog, time intelligence, review capacity, data quality, workload balance and executive exceptions. Redundant measures were not added to inflate the number.

## How did you avoid leakage between synthetic findings and workplace achievements?

The generator uses deterministic synthetic identifiers and documented simulated relationships. The README and insight files label results as portfolio demonstrations rather than employer results, and automated privacy checks scan for employer terms, emails, local user paths and credential patterns.

## Why use synthetic data?

Insurance claims are sensitive. Synthetic data allows realistic modelling, quality scenarios and business questions to be demonstrated without exposing customers, policies, claims, internal systems or employer-confidential information.

## How does the data-quality pipeline work?

The generator produces a canonical dataset plus controlled raw-data defects. Validation independently detects each seeded condition and creates a row-level audit. The clean build applies explicit corrections, removes only known later duplicates, enforces invariants and reconciles paid plus reserve to incurred.

## Why is fraud risk described as review prioritization?

A risk score is a triage signal, not proof. The project uses synthetic targets to demonstrate queue precision, recall and lift, but it retains analyst review and never automates repudiation, rejection or a fraud determination.

## How does the review-capacity simulator work?

A disconnected 5/10/15/20 percent parameter sets the share of highest-ranked claims that can enter the review queue. Measures then calculate selected volume, synthetic targets captured, review precision, synthetic-target recall, non-target review rate and lift against the base rate.

## How is CI/CD used?

GitHub Actions installs Python dependencies, regenerates the data, validates seeded defects, builds the clean schema and Power BI source, then runs project QA on pushes and pull requests to `main` and on manual dispatch. Permissions remain read-only for repository contents.

## What does automated QA test?

It tests required files, deterministic hashes, dataset grain, issue counts, financial reconciliation, dates, dimension keys, documented metrics, JSON and Microsoft schema declarations, PBIP references, PBIR page/visual structure, TMDL inventory, date-table semantics, relationship direction, DAX conventions, SQL/Python coverage, CI wiring, links, privacy and mockup labels.

## What requires Power BI Desktop verification?

Actual refresh, DAX compilation, rendered visuals, slicer and cross-filter behavior, bookmarks, reset actions, tooltips, drill-through, RLS effective identity, phone layouts, PBIX creation and genuine screenshots require a current Desktop host. Static QA does not claim those results.

## What would change for production deployment?

Local CSVs would move to governed lakehouse, warehouse or database sources; environment parameters and deployment pipelines would be added; RLS would use an identity-to-region bridge; refresh, lineage, monitoring, security and performance would be validated in the target tenant; and risk governance would include threshold monitoring, explainability, fairness review and operational oversight.

## Concise case study

**Problem:** Claims leaders need trustworthy visibility into cost, delay, reserves, SLA and constrained risk-review capacity.

**Approach:** Deterministic synthetic generation → validation → governed cleaning → star schema → Power Query → TMDL → DAX → PBIR → executive reporting → automated QA.

**Result:** A reproducible, privacy-safe decision-support project whose source and limitations can be inspected directly. Synthetic financial values are demonstration results, not workplace achievements.

