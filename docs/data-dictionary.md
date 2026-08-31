# Data dictionary

This dictionary covers every physical field delivered in the clean star-schema and quality-audit extracts.

| Field Name | Table | Data Type | Business Definition | Example | Nullable? | Derived? | Source Logic |
|---|---|---|---|---|---|---|---|
| Channel_Key | DimChannel | int64 | Channel key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Channel | DimChannel | string | Channel. | Broker | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Channel_Group | DimChannel | string | Channel group. | Intermediated | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Claim_Type_Key | DimClaimType | int64 | Claim type key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Claim_Type | DimClaimType | string | Claim type. | Collision | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Cause_Group | DimClaimType | string | Cause group. | General | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Date | DimDate | dateTime | Date. | 2024-01-01 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Date_Key | DimDate | int64 | Date key. | 20240101 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Year | DimDate | int64 | Year. | 2024 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Quarter | DimDate | string | Quarter. | Q1 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Month_Number | DimDate | int64 | Month number. | 1 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Month | DimDate | string | Month. | January | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Month_Short | DimDate | string | Month short. | Jan | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Year_Month | DimDate | string | Year month. | 2024-01 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Year_Month_Sort | DimDate | int64 | Year month sort. | 202401 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Week | DimDate | int64 | Week. | 1 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Day | DimDate | int64 | Day. | 1 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Day_Name | DimDate | string | Day name. | Monday | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Is_Month_End | DimDate | int64 | Is month end. | 0 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Handler_Key | DimHandler | int64 | Handler key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Handler | DimHandler | string | Handler. | Handler 01 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Team | DimHandler | string | Team. | Claims Team A | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Experience_Band | DimHandler | string | Experience band. | Experienced | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Monthly_Capacity | DimHandler | int64 | Monthly capacity. | 93 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Product_Key | DimProduct | int64 | Product key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Product | DimProduct | string | Product. | Motor | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Product_Description | DimProduct | string | Product description. | Personal and commercial motor claims | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Portfolio | DimProduct | string | Portfolio. | Short-term Insurance | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Region_Key | DimRegion | int64 | Region key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Region | DimRegion | string | Region. | Gauteng | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Operating_Zone | DimRegion | string | Operating zone. | Central | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Latitude | DimRegion | double | Latitude. | -26.2708 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Longitude | DimRegion | double | Longitude. | 28.1123 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Risk_Key | DimRisk | int64 | Risk key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Risk_Band | DimRisk | string | Risk band. | Low | No | Yes | Rule-based banding of synthetic amount, risk or complexity features. |
| Risk_Order | DimRisk | int64 | Risk order. | 1 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Definition | DimRisk | string | Definition. | Below 30 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Severity_Key | DimSeverity | int64 | Severity key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Severity_Band | DimSeverity | string | Severity band. | Low | No | Yes | Rule-based banding of synthetic amount, risk or complexity features. |
| Severity_Order | DimSeverity | int64 | Severity order. | 1 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Definition | DimSeverity | string | Definition. | Below R25k | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Status_Key | DimStatus | int64 | Status key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Claim_Status | DimStatus | string | Claim status. | Open | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Stage_Group | DimStatus | string | Stage group. | Intake | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Status_Order | DimStatus | int64 | Status order. | 1 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Open_Status_Flag | DimStatus | int64 | Open status flag. | 1 | No | No | Deterministic business rule or seeded synthetic outcome. |
| Supplier_Key | DimSupplier | int64 | Supplier key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Supplier | DimSupplier | string | Supplier. | Supplier Network 01 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Supplier_Type | DimSupplier | string | Supplier type. | Repair Network | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Home_Region_Key | DimSupplier | int64 | Home region key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Claim_ID | FactClaims | string | Synthetic claim identifier and fact-table grain. | CLM037119 | No | No | Deterministic synthetic identifier generated from the fixed seed. |
| Policy_ID | FactClaims | string | Synthetic policy identifier; policies may have multiple legitimate claims. | POL032857 | No | No | Deterministic synthetic identifier generated from the fixed seed. |
| Loss_Date | FactClaims | dateTime | Date on which the simulated insured event occurred. | 2024-02-19 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Report_Date | FactClaims | dateTime | Date on which the simulated claim was reported. | 2024-02-20 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Assignment_Date | FactClaims | dateTime | Date on which a handler was assigned. | 2024-02-21 | Yes | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Assessment_Date | FactClaims | dateTime | Date of simulated assessment completion. | 2024-03-07 | Yes | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Decision_Date | FactClaims | dateTime | Date of simulated claim decision. | 2024-03-20 | Yes | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Settlement_Date | FactClaims | dateTime | Date of settlement; blank for unsettled claims. | 2024-05-13 | Yes | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Loss_Date_Key | FactClaims | int64 | Loss date key. | 20240219 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Report_Date_Key | FactClaims | int64 | Report date key. | 20240220 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Settlement_Date_Key | FactClaims | int64 | Settlement date key. | 20240513 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Product_Key | FactClaims | int64 | Product key. | 2 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Region_Key | FactClaims | int64 | Region key. | 2 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Claim_Type_Key | FactClaims | int64 | Claim type key. | 7 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Handler_Key | FactClaims | int64 | Handler key. | 20 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Channel_Key | FactClaims | int64 | Channel key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Supplier_Key | FactClaims | int64 | Supplier key. | 10 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Status_Key | FactClaims | int64 | Status key. | 9 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Severity_Key | FactClaims | int64 | Severity key. | 4 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Risk_Key | FactClaims | int64 | Risk key. | 1 | No | Yes | Deterministic surrogate-key mapping to the conformed dimension. |
| Claim_Amount | FactClaims | decimal | Gross amount claimed in South African Rand. | 362929.6500 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Approved_Amount | FactClaims | decimal | Simplified approved amount in South African Rand. | 312894.6600 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Paid_Amount | FactClaims | decimal | Simplified paid amount in South African Rand. | 307072.2100 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Reserve_Amount | FactClaims | decimal | Simplified outstanding case reserve in South African Rand. | 0.0000 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Total_Incurred | FactClaims | decimal | Paid amount plus outstanding reserve; not actuarial ultimate loss. | 307072.2100 | No | Yes | Paid_Amount + Reserve_Amount. |
| Fraud_Risk_Score | FactClaims | double | Synthetic review-prioritization index from 0 to 100; not proof of fraud. | 16.8000 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Fraud_Referral_Flag | FactClaims | int64 | Indicates a simulated referral to a human investigation queue. | 0 | No | Yes | Deterministic business rule or seeded synthetic outcome. |
| Synthetic_Fraud_Target_Flag | FactClaims | int64 | Synthetic outcome used only to demonstrate precision, recall and lift. | 0 | No | Yes | Deterministic business rule or seeded synthetic outcome. |
| Risk_Rank_Percentile | FactClaims | double | Portfolio percentile of the synthetic risk score. | 0.1925 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Review_Priority | FactClaims | string | Operational priority band derived from risk score thresholds. | Routine | No | Yes | Rule-based banding of synthetic amount, risk or complexity features. |
| Reopened_Flag | FactClaims | int64 | Indicates that a claim was synthetically reopened. | 0 | No | Yes | Deterministic business rule or seeded synthetic outcome. |
| Complaint_Flag | FactClaims | int64 | Indicates a simulated complaint linked to the claim. | 0 | No | Yes | Deterministic business rule or seeded synthetic outcome. |
| Documentation_Missing_Flag | FactClaims | int64 | Latent synthetic feature representing missing documentation during handling. | 0 | No | No | Deterministic business rule or seeded synthetic outcome. |
| SLA_Target_Days | FactClaims | int64 | Complexity-based simulated target cycle time. | 80 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Settlement_Days | FactClaims | double | Days from report to settlement; blank for unsettled claims. | 83.0000 | Yes | Yes | Calculated from validated lifecycle dates. |
| SLA_Met_Flag | FactClaims | int64 | One when the observed or open age is within the target, otherwise zero. | 0 | No | Yes | Deterministic business rule or seeded synthetic outcome. |
| Reporting_Delay_Days | FactClaims | int64 | Days from loss to report. | 1 | No | Yes | Calculated from validated lifecycle dates. |
| Prior_Claims_Count | FactClaims | int64 | Synthetic count of earlier claims for the policy. | 0 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Policy_Tenure_Months | FactClaims | int64 | Synthetic policy tenure at claim time. | 110 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Claim_Complexity | FactClaims | string | Standard, Moderate, Complex or Specialist operational band. | Complex | No | Yes | Rule-based banding of synthetic amount, risk or complexity features. |
| Open_Claim_Age_Days | FactClaims | int64 | Age at 2026-08-31 for non-terminal claims; zero for terminal claims. | 0 | No | Yes | Calculated from validated lifecycle dates. |
| Assignment_Days | FactClaims | double | Days from report to assignment. | 1.0000 | Yes | Yes | Calculated from validated lifecycle dates. |
| Assessment_Days | FactClaims | double | Days from assignment to assessment. | 15.0000 | Yes | Yes | Calculated from validated lifecycle dates. |
| Decision_Days | FactClaims | double | Days from assessment to decision. | 13.0000 | Yes | Yes | Calculated from validated lifecycle dates. |
| Lifecycle_Stage | FactClaims | string | Operational stage aligned to the current claim status. | Closed | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Ingestion_Batch | FactClaims | string | Synthetic monthly ingestion batch in YYYY-MM format. | 2024-02 | No | Yes | Generated from documented synthetic portfolio logic or dimension metadata. |
| Investigation_Capacity_Pct | ReviewCapacityScenario | int64 | Illustrative share of claims that can be selected for analyst review. | 5 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Claims_Selected | ReviewCapacityScenario | int64 | Claims included in the capacity-constrained synthetic review queue. | 3750 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Synthetic_Targets_Captured | ReviewCapacityScenario | int64 | Synthetic demonstration target events included in the selected queue. | 644 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Review_Precision | ReviewCapacityScenario | double | Synthetic target events divided by claims selected for review. | 0.1717 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Synthetic_Target_Recall | ReviewCapacityScenario | double | Share of all synthetic demonstration target events included in the selected queue. | 0.0963 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Non_Target_Review_Rate | ReviewCapacityScenario | double | Share of selected claims without the synthetic target flag; not a real false-positive rate. | 0.8283 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Lift_vs_Random | ReviewCapacityScenario | double | Review precision divided by the portfolio-wide synthetic target rate. | 1.9270 | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Issue_ID | data_quality_issues | string | Unique detected data-quality issue event. | DQ-00001 | No | No | Generated by the raw-data validation and remediation audit pipeline. |
| Claim_ID | data_quality_issues | string | Synthetic claim identifier and fact-table grain. | CLM026785 | No | No | Deterministic synthetic identifier generated from the fixed seed. |
| Issue_Type | data_quality_issues | string | Governed category of the detected defect. | Missing Region | No | No | Generated by the raw-data validation and remediation audit pipeline. |
| Severity | data_quality_issues | string | Operational severity assigned to the quality issue. | High | No | No | Generated from documented synthetic portfolio logic or dimension metadata. |
| Original_Value | data_quality_issues | string | Defective raw value as detected. | <blank> | No | No | Generated by the raw-data validation and remediation audit pipeline. |
| Corrected_Value | data_quality_issues | string | Value used by the deterministic correction pipeline. | Free State | No | No | Generated by the raw-data validation and remediation audit pipeline. |
| Resolution | data_quality_issues | string | Plain-language remediation applied by the clean build. | Restored from the valid Region_Key mapping | No | No | Generated by the raw-data validation and remediation audit pipeline. |
