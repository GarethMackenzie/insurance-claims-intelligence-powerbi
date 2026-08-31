# Data model

![Star schema](../assets/data-model.svg)

`FactClaims` is at one row per synthetic claim after deduplication. It joins to ten conformed dimensions through surrogate keys and a primary active loss-date relationship. Report-date and settlement-date relationships to `DimDate` are inactive role-playing paths for measures that need `USERELATIONSHIP`.

| From (many) | To (one) | Active | Filter direction | Purpose |
|---|---|---:|---|---|
| FactClaims.Loss_Date | DimDate.Date | Yes | Single | Primary time intelligence |
| FactClaims.Report_Date | DimDate.Date | No | Single | Role-playing report date |
| FactClaims.Settlement_Date | DimDate.Date | No | Single | Role-playing settlement date |
| FactClaims.Product_Key | DimProduct.Product_Key | Yes | Single | Product analysis |
| FactClaims.Region_Key | DimRegion.Region_Key | Yes | Single | Provincial analysis |
| FactClaims.Claim_Type_Key | DimClaimType.Claim_Type_Key | Yes | Single | Cause analysis |
| FactClaims.Handler_Key | DimHandler.Handler_Key | Yes | Single | Workload scorecard |
| FactClaims.Channel_Key | DimChannel.Channel_Key | Yes | Single | Channel analysis |
| FactClaims.Supplier_Key | DimSupplier.Supplier_Key | Yes | Single | Supplier analysis |
| FactClaims.Status_Key | DimStatus.Status_Key | Yes | Single | Lifecycle stage |
| FactClaims.Severity_Key | DimSeverity.Severity_Key | Yes | Single | Severity band |
| FactClaims.Risk_Key | DimRisk.Risk_Key | Yes | Single | Risk band |
| DataQualityIssues.Claim_ID | FactClaims.Claim_ID | Yes | Single | Batch and segment context for raw audit issues |

The model contains **13 relationships**. No bidirectional filter is used. `Measures`, `Investigation Capacity`, and `Analysis Metric` are disconnected semantic helper tables. The audit relationship deliberately treats the unique claim ID in `FactClaims` as the one-side so claim batch and segment filters can contextualize quality issues.

`Total_Incurred` is a simplified paid-plus-case-reserve value. It is not an actuarial ultimate-loss estimate.
