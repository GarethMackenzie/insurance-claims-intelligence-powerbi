# Architecture

![Solution architecture](../assets/architecture.svg)

The solution is a local, file-backed PBIP portfolio demonstration. `generate_synthetic_claims.py` produces a reproducible raw extract. `validate_data.py` independently verifies every controlled defect and writes a row-level audit log. `build_clean_dataset.py` applies the governed corrections, enforces business rules, and materializes a star schema. Power Query expressions load those governed extracts into the TMDL semantic model; 79 explicit DAX measures support eight PBIR report pages.

The model uses Power BI Project source files rather than a fabricated PBIX. The project follows Microsoft's current PBIP properties, PBIR definition and semantic-model definition schema URLs embedded in each JSON file.

Microsoft references: [Power BI Projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR report project files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [enhanced PBIR](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format), [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), and the [report 3.2.0 JSON Schema](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json).

## Runtime flow

1. Fixed seed `20260831` generates 75,000 synthetic claims.
2. A separate raw layer contains 2,150 controlled quality issue events and 150 duplicate rows.
3. Validation checks each condition and records the correction decision.
4. The clean build applies corrections, removes the later duplicates and verifies business invariants.
5. Ten dimensions and `FactClaims` are loaded through reusable M.
6. Single-direction relationships propagate dimension filters to the fact.
7. Explicit DAX measures power executive, operational, financial, regional, risk and quality views.

## Deployment boundary

The source is designed for Power BI Desktop. A production implementation would replace local CSVs with governed lakehouse, warehouse or database sources; add environment parameters and deployment pipelines; and validate security, refresh, lineage and performance in the target tenant.
