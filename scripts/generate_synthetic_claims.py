"""Generate a deterministic, synthetic South African insurance claims portfolio.

The raw extract deliberately contains a controlled set of quality defects. Every
seeded defect is recorded in a private-to-the-demo manifest so the validation and
cleaning stages can prove that the defect was detected and resolved.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 20260831
N_CLAIMS = 75_000
AS_OF_DATE = pd.Timestamp("2026-08-31")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"


REGIONS = [
    "Gauteng",
    "Western Cape",
    "KwaZulu-Natal",
    "Eastern Cape",
    "Free State",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
]
REGION_WEIGHTS = np.array([0.285, 0.185, 0.155, 0.085, 0.055, 0.060, 0.070, 0.065, 0.040])
CHANNELS = ["Broker", "Direct", "Digital", "Call Centre"]
STATUSES = [
    "Open",
    "Assessment",
    "Awaiting Documents",
    "Awaiting Supplier",
    "Under Investigation",
    "Approved",
    "Settled",
    "Rejected",
    "Closed",
]
CLAIM_TYPES = [
    "Collision",
    "Theft",
    "Weather",
    "Fire",
    "Liability",
    "Glass",
    "Hail",
    "Flood",
    "Accidental Damage",
]


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-value))


def _date_strings(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y-%m-%d").fillna("")


def build_canonical_claims() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n = N_CLAIMS

    calendar = pd.date_range("2024-01-01", AS_OF_DATE, freq="D")
    month_index = np.asarray((calendar.year - 2024) * 12 + calendar.month, dtype=float)
    trend = 1 + 0.012 * month_index
    summer_weather = np.where(calendar.month.isin([1, 2, 11, 12]), 1.14, 1.0)
    day_weights = trend * summer_weather
    day_weights = day_weights / day_weights.sum()
    loss_dates = pd.to_datetime(rng.choice(calendar.values, size=n, p=day_weights))

    product = rng.choice(["Motor", "Agricultural"], size=n, p=[0.72, 0.28])
    region = rng.choice(REGIONS, size=n, p=REGION_WEIGHTS)

    claim_type = np.empty(n, dtype=object)
    motor_mask = product == "Motor"
    claim_type[motor_mask] = rng.choice(
        ["Collision", "Theft", "Glass", "Hail", "Fire", "Liability", "Flood"],
        size=motor_mask.sum(),
        p=[0.37, 0.17, 0.18, 0.12, 0.055, 0.065, 0.04],
    )
    agri_mask = ~motor_mask
    agri_prob = np.array([0.27, 0.20, 0.17, 0.12, 0.07, 0.10, 0.04, 0.03])
    winter = np.isin(pd.DatetimeIndex(loss_dates[agri_mask]).month, [5, 6, 7, 8])
    summer = np.isin(pd.DatetimeIndex(loss_dates[agri_mask]).month, [1, 2, 11, 12])
    agri_types = np.array(["Weather", "Hail", "Flood", "Fire", "Theft", "Accidental Damage", "Liability", "Collision"])
    agri_draws = []
    for is_winter, is_summer in zip(winter, summer):
        p = agri_prob.copy()
        if is_summer:
            p[[0, 1, 2]] *= 1.35
        if is_winter:
            p[[0, 3]] *= 1.18
        p /= p.sum()
        agri_draws.append(rng.choice(agri_types, p=p))
    claim_type[agri_mask] = agri_draws

    channel = np.where(
        product == "Agricultural",
        rng.choice(CHANNELS, size=n, p=[0.58, 0.14, 0.10, 0.18]),
        rng.choice(CHANNELS, size=n, p=[0.27, 0.25, 0.29, 0.19]),
    )

    amount_base = {
        "Collision": 58_000,
        "Theft": 92_000,
        "Weather": 145_000,
        "Fire": 230_000,
        "Liability": 115_000,
        "Glass": 11_500,
        "Hail": 78_000,
        "Flood": 175_000,
        "Accidental Damage": 72_000,
    }
    base = np.array([amount_base[value] for value in claim_type], dtype=float)
    base *= np.where(product == "Agricultural", 1.28, 1.0)
    base *= np.array(
        [
            {
                "Gauteng": 1.08,
                "Western Cape": 1.06,
                "KwaZulu-Natal": 1.02,
                "Eastern Cape": 0.96,
                "Free State": 0.95,
                "Limpopo": 0.94,
                "Mpumalanga": 1.00,
                "North West": 0.97,
                "Northern Cape": 1.01,
            }[value]
            for value in region
        ]
    )
    severity_trend = np.asarray(1 + 0.0075 * ((loss_dates.year - 2024) * 12 + loss_dates.month - 1), dtype=float)
    weather_shock = np.where(
        np.isin(claim_type, ["Weather", "Hail", "Flood"]) &
        np.isin(loss_dates.month, [1, 2, 11, 12]),
        1.22,
        1.0,
    )
    claim_amount = base * severity_trend * weather_shock * rng.lognormal(mean=-0.12, sigma=0.72, size=n)
    catastrophe = (
        (product == "Agricultural")
        & np.isin(claim_type, ["Weather", "Hail", "Flood", "Fire"])
        & (rng.random(n) < 0.025)
    )
    claim_amount[catastrophe] *= rng.uniform(2.5, 6.0, catastrophe.sum())
    claim_amount = np.clip(claim_amount, 2_500, 4_500_000).round(2)

    severity_band = pd.cut(
        claim_amount,
        bins=[-np.inf, 25_000, 100_000, 250_000, np.inf],
        labels=["Low", "Moderate", "High", "Large Loss"],
    ).astype(str)
    complexity_points = (
        (claim_amount >= 100_000).astype(int)
        + (claim_amount >= 250_000).astype(int)
        + np.isin(claim_type, ["Fire", "Liability", "Flood", "Weather"]).astype(int)
        + (product == "Agricultural").astype(int)
    )
    complexity = np.select(
        [complexity_points <= 1, complexity_points == 2, complexity_points == 3],
        ["Standard", "Moderate", "Complex"],
        default="Specialist",
    )

    policy_numeric = rng.integers(1, 48_501, size=n)
    policy_id = np.array([f"POL{value:06d}" for value in policy_numeric])
    prior_claims = pd.Series(policy_id).groupby(policy_id).cumcount().clip(upper=6).to_numpy()
    prior_claims = np.minimum(prior_claims + rng.binomial(1, 0.17, n), 7)
    policy_tenure = np.clip(rng.gamma(3.2, 17.0, n) + prior_claims * 7, 1, 240).round().astype(int)

    reporting_delay = rng.poisson(1.6, n)
    reporting_delay += np.where(channel == "Broker", rng.binomial(2, 0.22, n), 0)
    reporting_delay += np.where(claim_type == "Theft", rng.binomial(2, 0.35, n), 0)
    reporting_delay = np.clip(reporting_delay, 0, 24)
    report_dates = loss_dates + pd.to_timedelta(reporting_delay, unit="D")
    report_dates = pd.DatetimeIndex(np.minimum(report_dates.values, AS_OF_DATE.to_datetime64()))
    reporting_delay = (report_dates - loss_dates).days

    handler_key = rng.integers(1, 31, size=n)
    supplier_key = rng.integers(1, 46, size=n)
    assignment_delay = rng.integers(0, 4, size=n) + (report_dates.year >= 2026).astype(int)
    assignment_dates = report_dates + pd.to_timedelta(assignment_delay, unit="D")
    assessment_delay = rng.integers(2, 9, size=n) + complexity_points * rng.integers(1, 4, size=n)
    assessment_dates = assignment_dates + pd.to_timedelta(assessment_delay, unit="D")

    documentation_missing = rng.random(n) < (0.07 + 0.045 * (channel == "Broker") + 0.035 * (product == "Agricultural"))
    decision_delay = rng.integers(3, 13, size=n) + complexity_points * rng.integers(2, 7, size=n)
    decision_delay += documentation_missing * rng.integers(6, 23, size=n)
    decision_dates = assessment_dates + pd.to_timedelta(decision_delay, unit="D")

    backlog_factor = (
        ((report_dates >= pd.Timestamp("2025-04-01")) & (report_dates <= pd.Timestamp("2025-08-31"))).astype(int)
        + ((report_dates >= pd.Timestamp("2026-02-01")) & (report_dates <= pd.Timestamp("2026-06-30"))).astype(int)
    )
    target_cycle = (
        9
        + complexity_points * 12
        + np.select(
            [severity_band == "Moderate", severity_band == "High", severity_band == "Large Loss"],
            [5, 13, 28],
            default=0,
        )
        + documentation_missing * 15
        + backlog_factor * rng.integers(5, 17, size=n)
        + rng.gamma(2.2, 4.0, n)
    ).round().astype(int)
    target_cycle = np.clip(target_cycle, 4, 220)
    proposed_settlement = report_dates + pd.to_timedelta(target_cycle, unit="D")

    status = np.empty(n, dtype=object)
    mature = proposed_settlement <= AS_OF_DATE
    resolved = mature & (rng.random(n) < np.where(complexity_points >= 3, 0.86, 0.94))
    resolved_draw = rng.choice(["Settled", "Closed", "Rejected"], size=resolved.sum(), p=[0.67, 0.25, 0.08])
    status[resolved] = resolved_draw
    open_draw = rng.choice(
        ["Open", "Assessment", "Awaiting Documents", "Awaiting Supplier", "Under Investigation", "Approved"],
        size=(~resolved).sum(),
        p=[0.19, 0.15, 0.22, 0.17, 0.12, 0.15],
    )
    status[~resolved] = open_draw
    status[documentation_missing & ~resolved & (rng.random(n) < 0.52)] = "Awaiting Documents"

    settlement_dates = pd.Series(pd.NaT, index=np.arange(n), dtype="datetime64[ns]")
    paid_mask = np.isin(status, ["Settled", "Closed"])
    settlement_dates.loc[paid_mask] = proposed_settlement[paid_mask]
    decision_dates = pd.Series(decision_dates)
    decision_dates.loc[decision_dates > AS_OF_DATE] = pd.NaT
    assessment_dates = pd.Series(assessment_dates)
    assessment_dates.loc[assessment_dates > AS_OF_DATE] = pd.NaT
    assignment_dates = pd.Series(assignment_dates)
    assignment_dates.loc[assignment_dates > AS_OF_DATE] = pd.NaT

    approval_ratio = np.clip(rng.normal(0.91, 0.09, n), 0.48, 1.03)
    approved_amount = (claim_amount * approval_ratio).round(2)
    approved_amount[status == "Rejected"] = 0
    paid_ratio = np.where(paid_mask, np.clip(rng.normal(0.985, 0.025, n), 0.82, 1.0), 0.0)
    paid_ratio = np.where(status == "Approved", rng.uniform(0.05, 0.35, n), paid_ratio)
    paid_amount = (approved_amount * paid_ratio).round(2)
    reserve_uplift = np.where(complexity_points >= 3, 1.08, 1.02)
    reserve_amount = np.where(
        paid_mask | (status == "Rejected"),
        np.maximum(approved_amount - paid_amount, 0),
        np.maximum(approved_amount * reserve_uplift - paid_amount, claim_amount * 0.12),
    ).round(2)
    reserve_amount[paid_mask] = 0
    total_incurred = (paid_amount + reserve_amount).round(2)

    settlement_days = np.full(n, np.nan)
    settlement_days[paid_mask] = (settlement_dates.loc[paid_mask].to_numpy() - report_dates[paid_mask].to_numpy()).astype("timedelta64[D]").astype(int)
    open_age = np.where(
        np.isin(status, ["Settled", "Closed", "Rejected"]),
        0,
        np.maximum((AS_OF_DATE - report_dates).days, 0),
    )
    sla_target = np.select(
        [complexity == "Standard", complexity == "Moderate", complexity == "Complex"],
        [35, 55, 80],
        default=110,
    )
    observed_cycle = np.where(np.isnan(settlement_days), open_age, settlement_days)
    sla_met = (observed_cycle <= sla_target).astype(int)

    risk_logit = (
        -3.35
        + 0.115 * reporting_delay
        + 0.31 * np.minimum(prior_claims, 4)
        + 0.72 * (claim_type == "Theft")
        + 0.35 * (claim_type == "Fire")
        + 0.43 * (claim_amount >= 250_000)
        + 0.28 * np.isin(channel, ["Digital", "Direct"])
        + 0.37 * (policy_tenure < 9)
        + 0.22 * np.isin(region, ["Gauteng", "KwaZulu-Natal"])
    )
    true_probability = np.clip(_sigmoid(risk_logit), 0.006, 0.72)
    synthetic_fraud_target = (rng.random(n) < true_probability).astype(int)
    # The score is a prioritization index, not a calibrated fraud probability.
    score_probability = _sigmoid(risk_logit + 1.6 + rng.normal(0, 0.72, n))
    fraud_risk_score = np.clip(score_probability * 100, 1, 99.8).round(1)
    fraud_referral = ((fraud_risk_score >= 70) | ((fraud_risk_score >= 58) & (claim_amount >= 250_000))).astype(int)
    risk_band = pd.cut(
        fraud_risk_score,
        bins=[-np.inf, 30, 55, 75, np.inf],
        labels=["Low", "Moderate", "High", "Critical"],
    ).astype(str)
    risk_rank_percentile = pd.Series(fraud_risk_score).rank(method="first", pct=True).round(6).to_numpy()
    review_priority = pd.cut(
        fraud_risk_score,
        bins=[-np.inf, 55, 70, 85, np.inf],
        labels=["Routine", "Monitor", "Priority", "Immediate"],
    ).astype(str)

    reopened = (
        rng.random(n)
        < (0.028 + 0.025 * (complexity_points >= 3) + 0.018 * documentation_missing)
    ).astype(int)
    complaint = (
        rng.random(n)
        < (0.018 + 0.065 * (sla_met == 0) + 0.025 * reopened + 0.012 * documentation_missing)
    ).astype(int)

    product_key = np.where(product == "Motor", 1, 2)
    region_key_map = {name: i + 1 for i, name in enumerate(REGIONS)}
    claim_type_key_map = {name: i + 1 for i, name in enumerate(CLAIM_TYPES)}
    channel_key_map = {name: i + 1 for i, name in enumerate(CHANNELS)}
    status_key_map = {name: i + 1 for i, name in enumerate(STATUSES)}
    severity_key_map = {"Low": 1, "Moderate": 2, "High": 3, "Large Loss": 4}
    risk_key_map = {"Low": 1, "Moderate": 2, "High": 3, "Critical": 4}

    df = pd.DataFrame(
        {
            "Claim_ID": [f"CLM{i:06d}" for i in range(1, n + 1)],
            "Policy_ID": policy_id,
            "Loss_Date": loss_dates,
            "Report_Date": report_dates,
            "Assignment_Date": assignment_dates,
            "Assessment_Date": assessment_dates,
            "Decision_Date": decision_dates,
            "Settlement_Date": settlement_dates,
            "Product_Key": product_key,
            "Region_Key": [region_key_map[value] for value in region],
            "Claim_Type_Key": [claim_type_key_map[value] for value in claim_type],
            "Handler_Key": handler_key,
            "Channel_Key": [channel_key_map[value] for value in channel],
            "Supplier_Key": supplier_key,
            "Status_Key": [status_key_map[value] for value in status],
            "Severity_Key": [severity_key_map[value] for value in severity_band],
            "Risk_Key": [risk_key_map[value] for value in risk_band],
            "Product": product,
            "Region": region,
            "Claim_Type": claim_type,
            "Handler": [f"Handler {value:02d}" for value in handler_key],
            "Channel": channel,
            "Supplier": [f"Supplier Network {value:02d}" for value in supplier_key],
            "Claim_Status": status,
            "Claim_Amount": claim_amount,
            "Approved_Amount": approved_amount,
            "Paid_Amount": paid_amount,
            "Reserve_Amount": reserve_amount,
            "Total_Incurred": total_incurred,
            "Fraud_Risk_Score": fraud_risk_score,
            "Fraud_Referral_Flag": fraud_referral,
            "Synthetic_Fraud_Target_Flag": synthetic_fraud_target,
            "Risk_Rank_Percentile": risk_rank_percentile,
            "Review_Priority": review_priority,
            "Reopened_Flag": reopened,
            "Complaint_Flag": complaint,
            "Documentation_Missing_Flag": documentation_missing.astype(int),
            "SLA_Target_Days": sla_target,
            "Settlement_Days": settlement_days,
            "SLA_Met_Flag": sla_met,
            "Reporting_Delay_Days": reporting_delay,
            "Prior_Claims_Count": prior_claims,
            "Policy_Tenure_Months": policy_tenure,
            "Claim_Complexity": complexity,
            "Severity_Band": severity_band,
            "Risk_Band": risk_band,
            "Open_Claim_Age_Days": open_age,
            "Ingestion_Batch": pd.DatetimeIndex(report_dates).strftime("%Y-%m"),
        }
    )
    for column in [
        "Loss_Date",
        "Report_Date",
        "Assignment_Date",
        "Assessment_Date",
        "Decision_Date",
        "Settlement_Date",
    ]:
        df[column] = _date_strings(df[column])
    return df


def seed_quality_issues(canonical: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED + 17)
    raw = canonical.copy()
    raw.insert(0, "_Raw_Row_ID", np.arange(1, len(raw) + 1))
    shuffled = rng.permutation(len(raw))
    cursor = 0
    manifest: list[dict[str, object]] = []

    def allocate(count: int) -> np.ndarray:
        nonlocal cursor
        chosen = shuffled[cursor : cursor + count]
        cursor += count
        return chosen

    def add_issues(
        issue_type: str,
        column: str,
        indices: np.ndarray,
        replacement,
        severity: str,
        resolution: str,
    ) -> None:
        for idx in indices:
            corrected = raw.at[idx, column]
            bad = replacement(corrected, idx) if callable(replacement) else replacement
            raw.at[idx, column] = bad
            manifest.append(
                {
                    "Seed_ID": f"SEED-{len(manifest) + 1:05d}",
                    "Raw_Row_ID": int(raw.at[idx, "_Raw_Row_ID"]),
                    "Claim_ID": raw.at[idx, "Claim_ID"],
                    "Column_Name": column,
                    "Issue_Type": issue_type,
                    "Severity": severity,
                    "Original_Value": "<blank>" if pd.isna(bad) or str(bad) == "" else str(bad),
                    "Corrected_Value": "<blank>" if pd.isna(corrected) or str(corrected) == "" else str(corrected),
                    "Resolution": resolution,
                }
            )

    add_issues("Missing Region", "Region", allocate(200), "", "High", "Restored from the valid Region_Key mapping")
    add_issues("Missing Claim Amount", "Claim_Amount", allocate(180), np.nan, "Critical", "Restored the deterministic source amount")
    add_issues("Negative Claim Amount", "Claim_Amount", allocate(220), lambda value, _: -abs(float(value)), "Critical", "Replaced with the validated positive source amount")
    add_issues("Blank Channel", "Channel", allocate(180), "", "Medium", "Restored from the valid Channel_Key mapping")
    region_variants = {
        "Gauteng": "gauteng",
        "Western Cape": "Western cape",
        "KwaZulu-Natal": "KZN",
        "Eastern Cape": "Eastern cape",
        "Free State": "Free state",
        "Limpopo": "LIMPOPO",
        "Mpumalanga": "Mpumalanga ",
        "North West": "North-West",
        "Northern Cape": "Northern cape",
    }
    add_issues("Inconsistent Region Naming", "Region", allocate(250), lambda value, _: region_variants[str(value)], "Medium", "Standardized to the governed province name")
    status_variants = {
        "Open": "OPEN",
        "Assessment": "assessment",
        "Awaiting Documents": "Awaiting docs",
        "Awaiting Supplier": "Awaiting supplier",
        "Under Investigation": "under investigation",
        "Approved": "APPROVED",
        "Settled": "settled",
        "Rejected": "REJECTED",
        "Closed": "closed",
    }
    add_issues("Inconsistent Claim Status", "Claim_Status", allocate(250), lambda value, _: status_variants[str(value)], "Medium", "Mapped to the controlled status vocabulary")
    add_issues(
        "Incorrect Date Ordering",
        "Report_Date",
        allocate(200),
        lambda _value, idx: (pd.Timestamp(raw.at[idx, "Loss_Date"]) - pd.Timedelta(days=int(rng.integers(1, 6)))).strftime("%Y-%m-%d"),
        "Critical",
        "Restored the original report date after the loss date",
    )
    add_issues(
        "Future Settlement Date",
        "Settlement_Date",
        allocate(150),
        lambda _value, _idx: (AS_OF_DATE + pd.Timedelta(days=int(rng.integers(1, 91)))).strftime("%Y-%m-%d"),
        "Critical",
        "Restored the valid settlement date or blank open-claim state",
    )
    add_issues("Whitespace", "Channel", allocate(150), lambda value, _: f"  {value} ", "Low", "Trimmed leading and trailing whitespace")
    add_issues("Mixed Capitalization", "Claim_Type", allocate(120), lambda value, _: str(value).lower(), "Low", "Standardized capitalization")
    add_issues("Invalid Claim Type", "Claim_Type", allocate(100), "Impact Event", "High", "Restored from the valid Claim_Type_Key mapping")

    duplicate_sources = shuffled[cursor : cursor + 150]
    duplicate_rows = raw.loc[duplicate_sources].copy()
    duplicate_rows["_Raw_Row_ID"] = np.arange(len(raw) + 1, len(raw) + len(duplicate_rows) + 1)
    for _, row in duplicate_rows.iterrows():
        manifest.append(
            {
                "Seed_ID": f"SEED-{len(manifest) + 1:05d}",
                "Raw_Row_ID": int(row["_Raw_Row_ID"]),
                "Claim_ID": row["Claim_ID"],
                "Column_Name": "Claim_ID",
                "Issue_Type": "Duplicate Row",
                "Severity": "High",
                "Original_Value": row["Claim_ID"],
                "Corrected_Value": "<row removed>",
                "Resolution": "Removed the later duplicate raw row",
            }
        )
    raw = pd.concat([raw, duplicate_rows], ignore_index=True)
    raw = raw.sample(frac=1, random_state=SEED + 23).reset_index(drop=True)
    manifest_df = pd.DataFrame(manifest)
    return raw, manifest_df


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    canonical = build_canonical_claims()
    raw, manifest = seed_quality_issues(canonical)
    raw.to_csv(RAW_DIR / "claims_raw.csv", index=False)
    manifest.to_csv(DATA_DIR / "seeded_quality_manifest.csv", index=False)
    metadata = {
        "synthetic": True,
        "seed": SEED,
        "as_of_date": AS_OF_DATE.strftime("%Y-%m-%d"),
        "canonical_claims": int(len(canonical)),
        "raw_rows": int(len(raw)),
        "seeded_issue_events": int(len(manifest)),
        "seeded_rows": int(manifest["Raw_Row_ID"].nunique()),
        "quality_issue_rate_vs_claims": round(len(manifest) / len(canonical), 6),
        "date_min": canonical["Loss_Date"].min(),
        "date_max": canonical["Loss_Date"].max(),
    }
    (DATA_DIR / "generation_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(
        f"Generated {len(canonical):,} synthetic claims, {len(raw):,} raw rows, "
        f"and {len(manifest):,} controlled issue events."
    )


if __name__ == "__main__":
    main()
