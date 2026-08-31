"""Resolve validated raw-data issues and build the claims star-schema extracts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_FILE = DATA_DIR / "raw" / "claims_raw.csv"
MANIFEST_FILE = DATA_DIR / "seeded_quality_manifest.csv"
ISSUES_FILE = DATA_DIR / "data_quality_issues.csv"
CLEAN_DIR = DATA_DIR / "clean"
AS_OF_DATE = pd.Timestamp("2026-08-31")

REGIONS = [
    (1, "Gauteng", "Central", -26.2708, 28.1123),
    (2, "Western Cape", "Coastal", -33.2278, 21.8569),
    (3, "KwaZulu-Natal", "Coastal", -28.5306, 30.8958),
    (4, "Eastern Cape", "Coastal", -32.2968, 26.4194),
    (5, "Free State", "Central", -28.4541, 26.7968),
    (6, "Limpopo", "Northern", -23.4013, 29.4179),
    (7, "Mpumalanga", "Northern", -25.5653, 30.5279),
    (8, "North West", "Central", -26.6639, 25.2838),
    (9, "Northern Cape", "Western", -29.0467, 21.8569),
]
CLAIM_TYPES = ["Collision", "Theft", "Weather", "Fire", "Liability", "Glass", "Hail", "Flood", "Accidental Damage"]
STATUSES = ["Open", "Assessment", "Awaiting Documents", "Awaiting Supplier", "Under Investigation", "Approved", "Settled", "Rejected", "Closed"]


def apply_manifest_corrections(raw: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    raw["_Raw_Row_ID"] = raw["_Raw_Row_ID"].astype(int)
    manifest["Raw_Row_ID"] = manifest["Raw_Row_ID"].astype(int)
    duplicates = set(manifest.loc[manifest["Issue_Type"] == "Duplicate Row", "Raw_Row_ID"])
    clean = raw.loc[~raw["_Raw_Row_ID"].isin(duplicates)].copy()
    for _, issue in manifest.loc[manifest["Issue_Type"] != "Duplicate Row"].iterrows():
        value = issue["Corrected_Value"]
        value = "" if value == "<blank>" else value
        mask = clean["_Raw_Row_ID"] == int(issue["Raw_Row_ID"])
        if mask.sum() != 1:
            raise RuntimeError(f"Correction target {issue['Raw_Row_ID']} is not unique.")
        clean.loc[mask, issue["Column_Name"]] = value
    clean = clean.drop(columns="_Raw_Row_ID")
    clean = clean.drop_duplicates(subset=["Claim_ID"], keep="first")
    return clean


def enforce_types_and_rules(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "Product_Key", "Region_Key", "Claim_Type_Key", "Handler_Key", "Channel_Key",
        "Supplier_Key", "Status_Key", "Severity_Key", "Risk_Key", "Claim_Amount",
        "Approved_Amount", "Paid_Amount", "Reserve_Amount", "Total_Incurred",
        "Fraud_Risk_Score", "Fraud_Referral_Flag", "Synthetic_Fraud_Target_Flag",
        "Risk_Rank_Percentile", "Reopened_Flag", "Complaint_Flag",
        "Documentation_Missing_Flag", "SLA_Target_Days", "Settlement_Days",
        "SLA_Met_Flag", "Reporting_Delay_Days", "Prior_Claims_Count",
        "Policy_Tenure_Months", "Open_Claim_Age_Days",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    date_columns = ["Loss_Date", "Report_Date", "Assignment_Date", "Assessment_Date", "Decision_Date", "Settlement_Date"]
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    if len(df) != 75_000 or not df["Claim_ID"].is_unique:
        raise RuntimeError("The clean dataset must contain exactly 75,000 unique claims.")
    if (df["Claim_Amount"] <= 0).any():
        raise RuntimeError("Positive claim amount rule failed after cleaning.")
    if (df["Report_Date"] < df["Loss_Date"]).any():
        raise RuntimeError("Date ordering rule failed after cleaning.")
    if (df["Settlement_Date"] > AS_OF_DATE).any():
        raise RuntimeError("Future settlement date rule failed after cleaning.")
    if df[["Region", "Channel", "Claim_Type", "Claim_Status"]].replace("", np.nan).isna().any().any():
        raise RuntimeError("Required categorical fields remain blank after cleaning.")
    if not set(df["Claim_Type"]).issubset(CLAIM_TYPES):
        raise RuntimeError("Invalid claim type remains after cleaning.")

    df["Loss_Date_Key"] = df["Loss_Date"].dt.strftime("%Y%m%d").astype(int)
    df["Report_Date_Key"] = df["Report_Date"].dt.strftime("%Y%m%d").astype(int)
    df["Settlement_Date_Key"] = df["Settlement_Date"].dt.strftime("%Y%m%d").fillna("0").astype(int)
    df["Assignment_Days"] = (df["Assignment_Date"] - df["Report_Date"]).dt.days
    df["Assessment_Days"] = (df["Assessment_Date"] - df["Assignment_Date"]).dt.days
    df["Decision_Days"] = (df["Decision_Date"] - df["Assessment_Date"]).dt.days
    df["Lifecycle_Stage"] = df["Claim_Status"]
    return df


def build_dimensions(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_date = pd.DataFrame({"Date": pd.date_range("2024-01-01", AS_OF_DATE, freq="D")})
    dim_date["Date_Key"] = dim_date["Date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["Year"] = dim_date["Date"].dt.year
    dim_date["Quarter"] = "Q" + dim_date["Date"].dt.quarter.astype(str)
    dim_date["Month_Number"] = dim_date["Date"].dt.month
    dim_date["Month"] = dim_date["Date"].dt.strftime("%B")
    dim_date["Month_Short"] = dim_date["Date"].dt.strftime("%b")
    dim_date["Year_Month"] = dim_date["Date"].dt.strftime("%Y-%m")
    dim_date["Year_Month_Sort"] = dim_date["Date"].dt.strftime("%Y%m").astype(int)
    dim_date["Week"] = dim_date["Date"].dt.isocalendar().week.astype(int)
    dim_date["Day"] = dim_date["Date"].dt.day
    dim_date["Day_Name"] = dim_date["Date"].dt.strftime("%A")
    dim_date["Is_Month_End"] = dim_date["Date"].dt.is_month_end.astype(int)

    dim_product = pd.DataFrame(
        [
            (1, "Motor", "Personal and commercial motor claims", "Short-term Insurance"),
            (2, "Agricultural", "Agricultural asset and weather-related claims", "Short-term Insurance"),
        ],
        columns=["Product_Key", "Product", "Product_Description", "Portfolio"],
    )
    dim_region = pd.DataFrame(REGIONS, columns=["Region_Key", "Region", "Operating_Zone", "Latitude", "Longitude"])
    dim_claim_type = pd.DataFrame(
        [(i + 1, value, "Weather-related" if value in {"Weather", "Hail", "Flood"} else "General") for i, value in enumerate(CLAIM_TYPES)],
        columns=["Claim_Type_Key", "Claim_Type", "Cause_Group"],
    )
    dim_handler = pd.DataFrame(
        {
            "Handler_Key": range(1, 31),
            "Handler": [f"Handler {i:02d}" for i in range(1, 31)],
            "Team": [f"Claims Team {chr(65 + ((i - 1) % 5))}" for i in range(1, 31)],
            "Experience_Band": ["Developing" if i % 5 == 0 else "Experienced" if i % 3 else "Senior" for i in range(1, 31)],
            "Monthly_Capacity": [86 + ((i * 7) % 29) for i in range(1, 31)],
        }
    )
    dim_channel = pd.DataFrame(
        [(1, "Broker", "Intermediated"), (2, "Direct", "Direct"), (3, "Digital", "Self-service"), (4, "Call Centre", "Assisted")],
        columns=["Channel_Key", "Channel", "Channel_Group"],
    )
    supplier_types = ["Repair Network", "Assessor", "Loss Adjuster", "Investigation", "Parts Network"]
    dim_supplier = pd.DataFrame(
        {
            "Supplier_Key": range(1, 46),
            "Supplier": [f"Supplier Network {i:02d}" for i in range(1, 46)],
            "Supplier_Type": [supplier_types[(i - 1) % len(supplier_types)] for i in range(1, 46)],
            "Home_Region_Key": [((i - 1) % 9) + 1 for i in range(1, 46)],
        }
    )
    stage_group = {
        "Open": "Intake", "Assessment": "Assessment", "Awaiting Documents": "Documentation",
        "Awaiting Supplier": "Supplier", "Under Investigation": "Investigation",
        "Approved": "Decision", "Settled": "Complete", "Rejected": "Complete", "Closed": "Complete",
    }
    dim_status = pd.DataFrame(
        [(i + 1, value, stage_group[value], i + 1, int(value not in {"Settled", "Rejected", "Closed"})) for i, value in enumerate(STATUSES)],
        columns=["Status_Key", "Claim_Status", "Stage_Group", "Status_Order", "Open_Status_Flag"],
    )
    dim_severity = pd.DataFrame(
        [(1, "Low", 1, "Below R25k"), (2, "Moderate", 2, "R25k–R100k"), (3, "High", 3, "R100k–R250k"), (4, "Large Loss", 4, "Above R250k")],
        columns=["Severity_Key", "Severity_Band", "Severity_Order", "Definition"],
    )
    dim_risk = pd.DataFrame(
        [(1, "Low", 1, "Below 30"), (2, "Moderate", 2, "30–54.9"), (3, "High", 3, "55–74.9"), (4, "Critical", 4, "75 and above")],
        columns=["Risk_Key", "Risk_Band", "Risk_Order", "Definition"],
    )
    return {
        "DimDate": dim_date,
        "DimProduct": dim_product,
        "DimRegion": dim_region,
        "DimClaimType": dim_claim_type,
        "DimHandler": dim_handler,
        "DimChannel": dim_channel,
        "DimSupplier": dim_supplier,
        "DimStatus": dim_status,
        "DimSeverity": dim_severity,
        "DimRisk": dim_risk,
    }


def build_fact(df: pd.DataFrame) -> pd.DataFrame:
    fact_columns = [
        "Claim_ID", "Policy_ID", "Loss_Date", "Report_Date", "Assignment_Date",
        "Assessment_Date", "Decision_Date", "Settlement_Date", "Loss_Date_Key",
        "Report_Date_Key", "Settlement_Date_Key", "Product_Key", "Region_Key",
        "Claim_Type_Key", "Handler_Key", "Channel_Key", "Supplier_Key", "Status_Key",
        "Severity_Key", "Risk_Key", "Claim_Amount", "Approved_Amount", "Paid_Amount",
        "Reserve_Amount", "Total_Incurred", "Fraud_Risk_Score", "Fraud_Referral_Flag",
        "Synthetic_Fraud_Target_Flag", "Risk_Rank_Percentile", "Review_Priority",
        "Reopened_Flag", "Complaint_Flag", "Documentation_Missing_Flag", "SLA_Target_Days",
        "Settlement_Days", "SLA_Met_Flag", "Reporting_Delay_Days", "Prior_Claims_Count",
        "Policy_Tenure_Months", "Claim_Complexity", "Open_Claim_Age_Days",
        "Assignment_Days", "Assessment_Days", "Decision_Days", "Lifecycle_Stage",
        "Ingestion_Batch",
    ]
    return df[fact_columns].copy()


def build_findings(df: pd.DataFrame, validation: dict) -> tuple[dict, list[dict]]:
    open_mask = ~df["Claim_Status"].isin(["Settled", "Rejected", "Closed"])
    settled_mask = df["Settlement_Days"].notna()
    high_risk = df["Risk_Band"].isin(["High", "Critical"])

    by_type = df.groupby("Claim_Type", as_index=False).agg(Claims=("Claim_ID", "count"), Total_Incurred=("Total_Incurred", "sum"))
    by_type["Exposure_Share"] = by_type["Total_Incurred"] / by_type["Total_Incurred"].sum()
    top_type = by_type.sort_values("Total_Incurred", ascending=False).iloc[0]

    current = df[(df["Loss_Date"] >= "2026-01-01") & (df["Loss_Date"] <= "2026-08-31")]
    prior = df[(df["Loss_Date"] >= "2025-01-01") & (df["Loss_Date"] <= "2025-08-31")]
    sev_current = current.groupby("Region")["Claim_Amount"].mean()
    sev_prior = prior.groupby("Region")["Claim_Amount"].mean()
    severity_change = ((sev_current / sev_prior) - 1).dropna().sort_values(ascending=False)
    leading_region = severity_change.index[0]
    leading_region_change = float(severity_change.iloc[0])

    aged_mask = open_mask & (df["Open_Claim_Age_Days"] >= 30)
    aged_reserve_share = float(df.loc[aged_mask, "Reserve_Amount"].sum() / max(df.loc[open_mask, "Reserve_Amount"].sum(), 1))
    aged_claim_share = float(aged_mask.sum() / max(open_mask.sum(), 1))

    status_sla = (
        df.loc[open_mask]
        .groupby("Claim_Status")
        .agg(Claims=("Claim_ID", "count"), SLA_Compliance=("SLA_Met_Flag", "mean"))
        .query("Claims >= 250")
        .sort_values("SLA_Compliance")
    )
    weakest_status = status_sla.index[0]
    weakest_sla = float(status_sla.iloc[0]["SLA_Compliance"])

    high_risk_region = (
        df.assign(High_Risk=high_risk.astype(int))
        .groupby("Region")
        .agg(Claims=("Claim_ID", "count"), High_Risk=("High_Risk", "sum"))
    )
    high_risk_region["Rate"] = high_risk_region["High_Risk"] / high_risk_region["Claims"]
    risk_region = high_risk_region["Rate"].idxmax()
    risk_region_rate = float(high_risk_region.loc[risk_region, "Rate"])

    product_cycle = df.loc[settled_mask].groupby("Product")["Settlement_Days"].median().sort_values(ascending=False)
    slow_product = product_cycle.index[0]
    slow_cycle = float(product_cycle.iloc[0])
    other_cycle = float(product_cycle.iloc[-1])

    complaint_sla = df.groupby("SLA_Met_Flag")["Complaint_Flag"].mean()
    missed_complaint = float(complaint_sla.get(0, 0))
    met_complaint = float(complaint_sla.get(1, 0))

    ranked = df.sort_values("Fraud_Risk_Score", ascending=False)
    capacity_rows = []
    for capacity in [5, 10, 15, 20]:
        selected = ranked.head(int(np.ceil(len(ranked) * capacity / 100)))
        captured = int(selected["Synthetic_Fraud_Target_Flag"].sum())
        total_target = int(df["Synthetic_Fraud_Target_Flag"].sum())
        precision = captured / len(selected)
        recall = captured / max(total_target, 1)
        base_rate = total_target / len(df)
        capacity_rows.append(
            {
                "Investigation_Capacity_Pct": capacity,
                "Claims_Selected": int(len(selected)),
                "Synthetic_Targets_Captured": captured,
                "Review_Precision": precision,
                "Synthetic_Target_Recall": recall,
                "Non_Target_Review_Rate": 1 - precision,
                "Lift_vs_Random": precision / max(base_rate, 0.000001),
            }
        )
    pd.DataFrame(capacity_rows).to_csv(CLEAN_DIR / "ReviewCapacityScenario.csv", index=False)
    cap10 = capacity_rows[1]

    findings = [
        {
            "title": f"{top_type['Claim_Type']} leads incurred exposure",
            "observation": f"{top_type['Claim_Type']} is the largest synthetic claim-type exposure.",
            "evidence": f"It contributes R{top_type['Total_Incurred']:,.0f}, or {top_type['Exposure_Share']:.1%}, of total incurred.",
            "business_implication": "Concentration in one cause category can amplify reserve and supplier-management pressure.",
            "possible_action": "Review severity drivers, coverage mix and supplier pathways for this category; treat the result as a portfolio signal, not causal proof.",
        },
        {
            "title": f"{leading_region} has the strongest comparable severity increase",
            "observation": "Average claim amount increased most in this province in the January–August comparison.",
            "evidence": f"Synthetic average severity is {leading_region_change:+.1%} versus January–August 2025.",
            "business_implication": "A sustained increase may put upward pressure on case reserves and claims budgets.",
            "possible_action": "Drill into product, claim type and large-loss mix before attributing the change to operations or pricing.",
        },
        {
            "title": "Aged open claims concentrate reserve exposure",
            "observation": "Claims open for 30 days or longer hold a larger share of reserves than their share of open volume.",
            "evidence": f"They represent {aged_claim_share:.1%} of open claims and {aged_reserve_share:.1%} of open-claim reserves.",
            "business_implication": "Backlog reduction focused on value as well as count may release more operational attention.",
            "possible_action": "Prioritize aged, high-reserve cases for structured case review and barrier removal.",
        },
        {
            "title": f"{weakest_status} is the weakest open-stage SLA segment",
            "observation": "This lifecycle status records the lowest simulated SLA compliance among material open stages.",
            "evidence": f"SLA compliance is {weakest_sla:.1%} for the segment.",
            "business_implication": "A stage-specific queue can create downstream settlement delay and complaints.",
            "possible_action": "Inspect documentation, supplier and allocation dependencies in the stage before changing capacity.",
        },
        {
            "title": f"High-risk concentration is greatest in {risk_region}",
            "observation": "This province has the highest share of claims in the High or Critical synthetic risk bands.",
            "evidence": f"The concentration is {risk_region_rate:.1%} of claims in the province.",
            "business_implication": "A capacity-constrained investigation team may need risk-based regional queue monitoring.",
            "possible_action": "Use the score only to prioritize review and combine it with analyst judgement; it does not determine fraud.",
        },
        {
            "title": f"{slow_product} claims have the longer median settlement cycle",
            "observation": "The settled-claim median differs between the two synthetic portfolios.",
            "evidence": f"{slow_product} records {slow_cycle:.0f} days versus {other_cycle:.0f} days for the other product.",
            "business_implication": "Portfolio mix and complexity should be considered when comparing operational performance.",
            "possible_action": "Segment capacity and SLA conversations by complexity rather than applying one productivity target.",
        },
        {
            "title": "SLA misses coincide with a higher complaint rate",
            "observation": "Complaint incidence is higher among claims outside the simulated SLA target.",
            "evidence": f"Complaint rate is {missed_complaint:.1%} for SLA misses versus {met_complaint:.1%} where SLA is met.",
            "business_implication": "Timeliness and customer-friction indicators should be managed together.",
            "possible_action": "Monitor the relationship as an operational correlation; do not infer causality from the synthetic data.",
        },
        {
            "title": "Risk ranking creates review-capacity lift",
            "observation": "The top 10% of synthetic risk scores captures more target events than random review would be expected to capture.",
            "evidence": f"At 10% capacity, simulated review precision is {cap10['Review_Precision']:.1%}, synthetic-target recall is {cap10['Synthetic_Target_Recall']:.1%}, and lift is {cap10['Lift_vs_Random']:.2f}×.",
            "business_implication": "Prioritization can help allocate scarce review capacity, subject to governance and human decision-making.",
            "possible_action": "Validate thresholds, monitor non-target reviews and retain analyst review before any operational action.",
        },
    ]

    metrics = {
        "as_of_date": AS_OF_DATE.strftime("%Y-%m-%d"),
        "claims": int(len(df)),
        "open_claims": int(open_mask.sum()),
        "settled_claims": int((df["Claim_Status"] == "Settled").sum()),
        "total_claim_amount": float(df["Claim_Amount"].sum()),
        "total_paid": float(df["Paid_Amount"].sum()),
        "outstanding_reserve": float(df["Reserve_Amount"].sum()),
        "total_incurred": float(df["Total_Incurred"].sum()),
        "average_severity": float(df["Claim_Amount"].mean()),
        "median_settlement_days": float(df.loc[settled_mask, "Settlement_Days"].median()),
        "average_settlement_days": float(df.loc[settled_mask, "Settlement_Days"].mean()),
        "p90_settlement_days": float(df.loc[settled_mask, "Settlement_Days"].quantile(0.9)),
        "sla_compliance": float(df["SLA_Met_Flag"].mean()),
        "high_risk_claims": int(high_risk.sum()),
        "high_risk_rate": float(high_risk.mean()),
        "fraud_referral_rate": float(df["Fraud_Referral_Flag"].mean()),
        "reopen_rate": float(df["Reopened_Flag"].mean()),
        "complaint_rate": float(df["Complaint_Flag"].mean()),
        "raw_rows": int(validation["raw_rows"]),
        "seeded_issues": int(validation["seeded_issue_events"]),
        "detected_issues": int(validation["detected_issue_events"]),
        "data_quality_score": float(1 - validation["detected_issue_events"] / validation["raw_rows"]),
        "date_min": df["Loss_Date"].min().strftime("%Y-%m-%d"),
        "date_max": df["Loss_Date"].max().strftime("%Y-%m-%d"),
        "capacity_scenarios": capacity_rows,
    }
    return metrics, findings


def main() -> None:
    if not all(path.exists() for path in [RAW_FILE, MANIFEST_FILE, ISSUES_FILE]):
        raise FileNotFoundError("Run generation and validation before the clean build.")
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
    manifest = pd.read_csv(MANIFEST_FILE, dtype=str, keep_default_na=False)
    clean = apply_manifest_corrections(raw, manifest)
    clean = enforce_types_and_rules(clean)
    dimensions = build_dimensions(clean)
    fact = build_fact(clean)

    date_columns = ["Loss_Date", "Report_Date", "Assignment_Date", "Assessment_Date", "Decision_Date", "Settlement_Date"]
    for column in date_columns:
        fact[column] = fact[column].dt.strftime("%Y-%m-%d").fillna("")
    fact.to_csv(CLEAN_DIR / "FactClaims.csv", index=False)
    for name, table in dimensions.items():
        if "Date" in table.columns:
            table["Date"] = pd.to_datetime(table["Date"]).dt.strftime("%Y-%m-%d")
        table.to_csv(CLEAN_DIR / f"{name}.csv", index=False)

    validation = json.loads((DATA_DIR / "validation_summary.json").read_text(encoding="utf-8"))
    metrics, findings = build_findings(clean, validation)
    (DATA_DIR / "portfolio_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (DATA_DIR / "executive_insights.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(f"Built FactClaims ({len(fact):,} rows) and {len(dimensions)} conformed dimensions.")


if __name__ == "__main__":
    main()
