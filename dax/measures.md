# DAX measure layer

The dedicated `Measures` table contains **79 explicit measures**. Implicit measures are discouraged in `model.tmdl`. Currency measures use South African Rand formatting, ratios use `DIVIDE`, and time intelligence uses the conformed `DimDate` table.

> Risk and target measures operate on synthetic demonstration labels. A risk score prioritizes human review; it does not determine fraud.

## Backlog

### 30+ Day Open Claims

Open claims aged at least 30 days.

```DAX
30+ Day Open Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ), KEEPFILTERS ( FactClaims[Open_Claim_Age_Days] >= 30 ) )
```

Format: `#,0`

### 60+ Day Open Claims

Open claims aged at least 60 days.

```DAX
60+ Day Open Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ), KEEPFILTERS ( FactClaims[Open_Claim_Age_Days] >= 60 ) )
```

Format: `#,0`

### Backlog %

Share of open claims aged at least 30 days.

```DAX
Backlog % = DIVIDE ( [30+ Day Open Claims], [Open Claims] )
```

Format: `0.0%`

### Awaiting Documents Claims

Claims awaiting documentation.

```DAX
Awaiting Documents Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 3 ) )
```

Format: `#,0`

### Awaiting Supplier Claims

Claims awaiting supplier activity.

```DAX
Awaiting Supplier Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 4 ) )
```

Format: `#,0`

## Data Quality

### Detected Data Quality Issues

Detected raw-data issue events.

```DAX
Detected Data Quality Issues = COUNTROWS ( DataQualityIssues )
```

Format: `#,0`

### Invalid Row Count

Distinct claims affected by a detected raw-data issue.

```DAX
Invalid Row Count = DISTINCTCOUNT ( DataQualityIssues[Claim_ID] )
```

Format: `#,0`

### Raw Rows

Rows in the generated raw extract, including controlled duplicates.

```DAX
Raw Rows = 75150
```

Format: `#,0`

### Duplicate Rate

Duplicate issue events divided by raw rows.

```DAX
Duplicate Rate = DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] = "Duplicate Row" ), [Raw Rows] )
```

Format: `0.0%`

### Missing Region %

Missing-region issue events divided by raw rows.

```DAX
Missing Region % = DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] = "Missing Region" ), [Raw Rows] )
```

Format: `0.0%`

### Invalid Amount Count

Missing or negative claim-amount issues.

```DAX
Invalid Amount Count = CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { "Missing Claim Amount", "Negative Claim Amount" } )
```

Format: `#,0`

### Invalid Date Count

Invalid ordering or future-date issue events.

```DAX
Invalid Date Count = CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { "Incorrect Date Ordering", "Future Settlement Date" } )
```

Format: `#,0`

### Completeness %

Completeness across three controlled required fields in the raw data.

```DAX
Completeness % = 1 - DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { "Missing Region", "Missing Claim Amount", "Blank Channel" } ), [Raw Rows] * 3 )
```

Format: `0.0%`

### Data Quality Score

Simple transparent quality index: one minus detected issue events per raw row.

```DAX
Data Quality Score = 1 - DIVIDE ( [Detected Data Quality Issues], [Raw Rows] )
```

Format: `0.0%`

## Executive Attention

### Executive Attention — Severity

Dynamic executive exception statement.

```DAX
Executive Attention — Severity = VAR Delta = [Severity YoY %]
RETURN IF ( ISBLANK ( Delta ), "Severity comparison unavailable", IF ( Delta >= 0, "▲ Severity " & FORMAT ( Delta, "0.0%" ) & " YoY", "▼ Severity " & FORMAT ( ABS ( Delta ), "0.0%" ) & " YoY" ) )
```

Format: `General`

### Executive Attention — SLA

Dynamic SLA exception statement.

```DAX
Executive Attention — SLA = VAR Delta = [SLA Variance vs PY]
RETURN IF ( ISBLANK ( Delta ), "SLA comparison unavailable", IF ( Delta >= 0, "▲ SLA compliance +" & FORMAT ( Delta, "0.0" ) & " pp", "▼ SLA compliance " & FORMAT ( Delta, "0.0" ) & " pp" ) )
```

Format: `General`

### Executive Attention — Backlog

Dynamic backlog exception statement.

```DAX
Executive Attention — Backlog = "▲ 30+ day backlog: " & FORMAT ( [30+ Day Open Claims], "#,0" ) & " claims (" & FORMAT ( [Backlog %], "0.0%" ) & ")"
```

Format: `General`

## Field Parameter

### Selected Metric Value

Metric selector used by root-cause and comparative visuals.

```DAX
Selected Metric Value = SWITCH ( SELECTEDVALUE ( 'Analysis Metric'[Analysis Metric], "Total Incurred" ), "Total Incurred", [Total Incurred], "Average Severity", [Average Severity], "Settlement Days", [Average Settlement Days], "SLA Compliance", [SLA Compliance %], "Fraud Referral Rate", [Fraud Referral Rate %], [Total Incurred] )
```

Format: `#,0.00`

## Financial

### Total Claim Amount

Gross synthetic claimed amount.

```DAX
Total Claim Amount = SUM ( FactClaims[Claim_Amount] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Total Approved

Approved synthetic amount.

```DAX
Total Approved = SUM ( FactClaims[Approved_Amount] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Total Paid

Paid synthetic amount.

```DAX
Total Paid = SUM ( FactClaims[Paid_Amount] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Outstanding Reserve

Outstanding simplified case reserve.

```DAX
Outstanding Reserve = SUM ( FactClaims[Reserve_Amount] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Total Incurred

Paid plus outstanding reserve; not an actuarial estimate.

```DAX
Total Incurred = SUM ( FactClaims[Total_Incurred] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Large Loss Count

Claims at or above R250,000.

```DAX
Large Loss Count = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Claim_Amount] >= 250000 ) )
```

Format: `#,0`

### Large Loss Exposure

Incurred exposure from large losses.

```DAX
Large Loss Exposure = CALCULATE ( [Total Incurred], KEEPFILTERS ( FactClaims[Claim_Amount] >= 250000 ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Reserve per Open Claim

Outstanding reserve per open claim.

```DAX
Reserve per Open Claim = DIVIDE ( [Outstanding Reserve], [Open Claims] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

## Handler Scorecard

### Handler Throughput Index

Relative throughput component; not a productivity judgement.

```DAX
Handler Throughput Index = DIVIDE ( [Claims Per Handler], CALCULATE ( [Claims Per Handler], ALL ( DimHandler ) ) )
```

Format: `0.00`

### Handler Service Index

Relative service component.

```DAX
Handler Service Index = DIVIDE ( [SLA Compliance %], CALCULATE ( [SLA Compliance %], ALL ( DimHandler ) ) )
```

Format: `0.00`

### Handler Quality Index

Relative quality component combining reopen and complaint signals.

```DAX
Handler Quality Index = DIVIDE ( 1 - [Reopen Rate %] - [Complaint Rate %], CALCULATE ( 1 - [Reopen Rate %] - [Complaint Rate %], ALL ( DimHandler ) ) )
```

Format: `0.00`

### Handler Complexity Index

Claim-value mix proxy for complexity; not a complete case-mix adjustment.

```DAX
Handler Complexity Index = DIVIDE ( AVERAGE ( FactClaims[Claim_Amount] ), CALCULATE ( [Average Severity], ALL ( DimHandler ) ) )
```

Format: `0.00`

### Balanced Effectiveness Score

Balanced workload-management demonstration; not an employee performance score.

```DAX
Balanced Effectiveness Score = VAR Throughput = MIN ( [Handler Throughput Index], 1.5 )
VAR Service = MIN ( [Handler Service Index], 1.5 )
VAR Quality = MIN ( [Handler Quality Index], 1.5 )
VAR Complexity = MIN ( [Handler Complexity Index], 1.5 )
RETURN 0.25 * Throughput + 0.35 * Service + 0.25 * Quality + 0.15 * Complexity
```

Format: `0.00`

## Operations

### Average Settlement Days

Average reporting-to-settlement days for settled claims.

```DAX
Average Settlement Days = AVERAGE ( FactClaims[Settlement_Days] )
```

Format: `0.0`

### Median Settlement Days

Median reporting-to-settlement days.

```DAX
Median Settlement Days = MEDIAN ( FactClaims[Settlement_Days] )
```

Format: `0`

### 90th Percentile Settlement Days

90th percentile reporting-to-settlement days.

```DAX
90th Percentile Settlement Days = PERCENTILEX.INC ( FILTER ( FactClaims, NOT ISBLANK ( FactClaims[Settlement_Days] ) ), FactClaims[Settlement_Days], 0.9 )
```

Format: `0`

### Average Reporting Delay

Average days from loss to report.

```DAX
Average Reporting Delay = AVERAGE ( FactClaims[Reporting_Delay_Days] )
```

Format: `0.0`

### Average Open Age

Average age of claims in governed open lifecycle statuses.

```DAX
Average Open Age = CALCULATE ( AVERAGE ( FactClaims[Open_Claim_Age_Days] ), KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ) )
```

Format: `0.0`

## Quality

### Reopen Rate %

Share of claims marked reopened.

```DAX
Reopen Rate % = DIVIDE ( SUM ( FactClaims[Reopened_Flag] ), [Total Claims] )
```

Format: `0.0%`

### Complaint Rate %

Share of claims with a simulated complaint flag.

```DAX
Complaint Rate % = DIVIDE ( SUM ( FactClaims[Complaint_Flag] ), [Total Claims] )
```

Format: `0.0%`

## Review Capacity

### Investigation Capacity %

Selected proportion of claims that the review team can investigate.

```DAX
Investigation Capacity % = DIVIDE ( SELECTEDVALUE ( 'Investigation Capacity'[Investigation Capacity], 10 ), 100 )
```

Format: `0.0%`

### Claims Selected for Review

Claims in the highest risk-score percentile within selected capacity.

```DAX
Claims Selected for Review = VAR Capacity = [Investigation Capacity %]
RETURN COUNTROWS ( FILTER ( VALUES ( FactClaims[Claim_ID] ), CALCULATE ( MAX ( FactClaims[Risk_Rank_Percentile] ) ) > 1 - Capacity ) )
```

Format: `#,0`

### Synthetic Targets Captured

Synthetic demonstration target events in the selected review queue.

```DAX
Synthetic Targets Captured = VAR Capacity = [Investigation Capacity %]
RETURN SUMX ( FILTER ( VALUES ( FactClaims[Claim_ID] ), CALCULATE ( MAX ( FactClaims[Risk_Rank_Percentile] ) ) > 1 - Capacity ), CALCULATE ( MAX ( FactClaims[Synthetic_Fraud_Target_Flag] ) ) )
```

Format: `#,0`

### Synthetic Target Events

Synthetic binary target used only to demonstrate prioritization metrics.

```DAX
Synthetic Target Events = SUM ( FactClaims[Synthetic_Fraud_Target_Flag] )
```

Format: `#,0`

### Review Precision

Synthetic target events divided by selected claims.

```DAX
Review Precision = DIVIDE ( [Synthetic Targets Captured], [Claims Selected for Review] )
```

Format: `0.0%`

### Synthetic Target Recall

Share of synthetic demonstration target events captured by the queue.

```DAX
Synthetic Target Recall = DIVIDE ( [Synthetic Targets Captured], [Synthetic Target Events] )
```

Format: `0.0%`

### Non-Target Review Rate

Selected claims without the synthetic target flag; this is not a real false-positive rate.

```DAX
Non-Target Review Rate = 1 - [Review Precision]
```

Format: `0.0%`

### Review Workload

Selected investigation queue volume.

```DAX
Review Workload = [Claims Selected for Review]
```

Format: `#,0`

### Base Synthetic Target Rate

Portfolio-wide synthetic target rate.

```DAX
Base Synthetic Target Rate = DIVIDE ( [Synthetic Target Events], [Total Claims] )
```

Format: `0.0%`

### Lift vs Random Review

Review precision divided by the portfolio target rate.

```DAX
Lift vs Random Review = DIVIDE ( [Review Precision], [Base Synthetic Target Rate] )
```

Format: `0.00×`

## Risk

### Fraud Referral Rate %

Share referred for review; referral does not determine fraud.

```DAX
Fraud Referral Rate % = DIVIDE ( SUM ( FactClaims[Fraud_Referral_Flag] ), [Total Claims] )
```

Format: `0.0%`

### High Risk Claims

Claims in High or Critical synthetic risk bands.

```DAX
High Risk Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Risk_Key] >= 3 ) )
```

Format: `#,0`

### High Risk Claims %

High/Critical risk share.

```DAX
High Risk Claims % = DIVIDE ( [High Risk Claims], [Total Claims] )
```

Format: `0.0%`

### Under Investigation Claims

Claims in the investigation queue.

```DAX
Under Investigation Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 5 ) )
```

Format: `#,0`

## Service

### SLA Compliance %

Share of claims within the simulated complexity-based SLA.

```DAX
SLA Compliance % = DIVIDE ( SUM ( FactClaims[SLA_Met_Flag] ), [Total Claims] )
```

Format: `0.0%`

## Severity

### Average Severity

Mean synthetic claim amount.

```DAX
Average Severity = AVERAGE ( FactClaims[Claim_Amount] )
```

Format: `R #,##0.00;[Red]-R #,##0.00;R 0.00`

### Median Severity

Median synthetic claim amount.

```DAX
Median Severity = MEDIAN ( FactClaims[Claim_Amount] )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### P90 Severity

90th percentile synthetic claim amount.

```DAX
P90 Severity = PERCENTILEX.INC ( FactClaims, FactClaims[Claim_Amount], 0.9 )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

## Time Intelligence

### Claims MTD

Month-to-date claims by loss date.

```DAX
Claims MTD = CALCULATE ( [Total Claims], DATESMTD ( DimDate[Date] ) )
```

Format: `#,0`

### Claims QTD

Quarter-to-date claims by loss date.

```DAX
Claims QTD = CALCULATE ( [Total Claims], DATESQTD ( DimDate[Date] ) )
```

Format: `#,0`

### Claims YTD

Year-to-date claims by loss date.

```DAX
Claims YTD = CALCULATE ( [Total Claims], DATESYTD ( DimDate[Date] ) )
```

Format: `#,0`

### Claims PY

Claims in the prior-year comparison period.

```DAX
Claims PY = CALCULATE ( [Total Claims], DATEADD ( DimDate[Date], -1, YEAR ) )
```

Format: `#,0`

### Claims YoY %

Year-over-year claims-volume change.

```DAX
Claims YoY % = VAR CurrentValue = [Total Claims]
VAR PriorValue = [Claims PY]
RETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )
```

Format: `0.0%`

### Incurred MTD

Month-to-date incurred.

```DAX
Incurred MTD = CALCULATE ( [Total Incurred], DATESMTD ( DimDate[Date] ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Incurred YTD

Year-to-date incurred.

```DAX
Incurred YTD = CALCULATE ( [Total Incurred], DATESYTD ( DimDate[Date] ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Incurred PY

Prior-year incurred comparison.

```DAX
Incurred PY = CALCULATE ( [Total Incurred], DATEADD ( DimDate[Date], -1, YEAR ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Incurred YoY %

Year-over-year incurred change.

```DAX
Incurred YoY % = VAR CurrentValue = [Total Incurred]
VAR PriorValue = [Incurred PY]
RETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )
```

Format: `0.0%`

### Severity PY

Prior-year average severity.

```DAX
Severity PY = CALCULATE ( [Average Severity], DATEADD ( DimDate[Date], -1, YEAR ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

### Severity YoY %

Year-over-year average severity change.

```DAX
Severity YoY % = VAR CurrentValue = [Average Severity]
VAR PriorValue = [Severity PY]
RETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )
```

Format: `0.0%`

### SLA Compliance PY

Prior-year SLA compliance.

```DAX
SLA Compliance PY = CALCULATE ( [SLA Compliance %], DATEADD ( DimDate[Date], -1, YEAR ) )
```

Format: `0.0%`

### SLA Variance vs PY

Percentage-point SLA change versus prior year.

```DAX
SLA Variance vs PY = 100 * ( [SLA Compliance %] - [SLA Compliance PY] )
```

Format: `0.0 pp`

### Rolling 12M Claims

Claims over the rolling 12 months ending in context.

```DAX
Rolling 12M Claims = CALCULATE ( [Total Claims], DATESINPERIOD ( DimDate[Date], MAX ( DimDate[Date] ), -12, MONTH ) )
```

Format: `#,0`

### Rolling 12M Incurred

Incurred over the rolling 12 months ending in context.

```DAX
Rolling 12M Incurred = CALCULATE ( [Total Incurred], DATESINPERIOD ( DimDate[Date], MAX ( DimDate[Date] ), -12, MONTH ) )
```

Format: `R #,##0;[Red]-R #,##0;R 0`

## Volume

### Total Claims

Distinct synthetic claims in filter context.

```DAX
Total Claims = DISTINCTCOUNT ( FactClaims[Claim_ID] )
```

Format: `#,0`

### Open Claims

Claims in governed open lifecycle statuses.

```DAX
Open Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ) )
```

Format: `#,0`

### Settled Claims

Claims in Settled status.

```DAX
Settled Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 7 ) )
```

Format: `#,0`

### Rejected Claims

Claims in Rejected status.

```DAX
Rejected Claims = CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 8 ) )
```

Format: `#,0`

### Claims per Policy

Claim frequency proxy for the synthetic portfolio.

```DAX
Claims per Policy = DIVIDE ( [Total Claims], DISTINCTCOUNT ( FactClaims[Policy_ID] ) )
```

Format: `0.00`

## Workload

### Active Handlers

Handlers represented by filtered claims.

```DAX
Active Handlers = DISTINCTCOUNT ( FactClaims[Handler_Key] )
```

Format: `#,0`

### Claims Per Handler

Filtered claims per active handler.

```DAX
Claims Per Handler = DIVIDE ( [Total Claims], [Active Handlers] )
```

Format: `0.0`

### Open Claims Per Handler

Open filtered workload per active handler.

```DAX
Open Claims Per Handler = DIVIDE ( [Open Claims], [Active Handlers] )
```

Format: `0.0`
