# Data quality challenge

        The raw layer contains **75,150 rows** for **75,000 canonical claims**. It includes **2,150 controlled issue events** (2.87% of canonical claim count). Validation detected all **2,150** events; the clean fact contains 75,000 unique positive-amount claims with valid primary date ordering.

        | Issue type | Detected events |
        |---|---:|
        | Blank Channel | 180 |
| Duplicate Row | 150 |
| Future Settlement Date | 150 |
| Inconsistent Claim Status | 250 |
| Inconsistent Region Naming | 250 |
| Incorrect Date Ordering | 200 |
| Invalid Claim Type | 100 |
| Missing Claim Amount | 180 |
| Missing Region | 200 |
| Mixed Capitalization | 120 |
| Negative Claim Amount | 220 |
| Whitespace | 150 |

        ## Controls

        - Preserve raw evidence and stable raw-row IDs.
        - Detect before correcting; fail the build if a seeded condition is not observed.
        - Quarantine logic is demonstrated in M; the executable build uses explicit correction records.
        - Remove only the known later duplicate rows.
        - Enforce positive amounts, valid date order, governed categories and unique claim grain.
        - Reconcile paid plus reserve to total incurred.

        `Data Quality Score` is a transparent portfolio-demo index: `1 - detected issue events / raw rows` = **97.1%**. It is not an industry standard.
