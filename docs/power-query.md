# Power Query design

The editable M sources are in [`powerquery/`](../powerquery/), and the model-level expressions are in [`expressions.tmdl`](../InsuranceClaimsIntelligence.SemanticModel/definition/expressions.tmdl).

## Query pattern

- `pProjectRoot` is a text parameter for the local repository root.
- `fnLoadCsv` centralizes UTF-8 CSV loading, header promotion and schema enforcement.
- `fnNormalizeText` performs null-safe trim and clean operations.
- `stg_ClaimsRaw` preserves source evidence and adds duplicate counts.
- `validation_rules` applies amount, date and controlled-vocabulary checks and assigns ACCEPT/QUARANTINE outcomes.
- `stg_ClaimsClean` enforces positive amounts, valid date ordering and one-row-per-claim grain.
- Table partitions load governed clean CSVs with explicit M table types.

The Python cleaning pipeline is the executable reference implementation for this repository. The M files demonstrate the corresponding Power Query staging, validation and reusable-function pattern without hiding the remediation audit trail.
