"""Detect the controlled quality problems in the raw synthetic claims extract."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_FILE = DATA_DIR / "raw" / "claims_raw.csv"
MANIFEST_FILE = DATA_DIR / "seeded_quality_manifest.csv"
AS_OF_DATE = pd.Timestamp("2026-08-31")
REGIONS = {
    "Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State",
    "Limpopo", "Mpumalanga", "North West", "Northern Cape",
}
CHANNELS = {"Broker", "Direct", "Digital", "Call Centre"}
STATUSES = {
    "Open", "Assessment", "Awaiting Documents", "Awaiting Supplier",
    "Under Investigation", "Approved", "Settled", "Rejected", "Closed",
}
CLAIM_TYPES = {
    "Collision", "Theft", "Weather", "Fire", "Liability", "Glass", "Hail",
    "Flood", "Accidental Damage",
}


def _blank(value: object) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def _detect(issue_type: str, row: pd.Series, raw: pd.DataFrame) -> bool:
    value = row.get("_Issue_Value", "")
    if issue_type == "Missing Region":
        return _blank(value)
    if issue_type == "Missing Claim Amount":
        return _blank(value)
    if issue_type == "Negative Claim Amount":
        return not _blank(value) and float(value) < 0
    if issue_type == "Blank Channel":
        return _blank(value)
    if issue_type == "Inconsistent Region Naming":
        return not _blank(value) and str(value) not in REGIONS
    if issue_type == "Inconsistent Claim Status":
        return not _blank(value) and str(value) not in STATUSES
    if issue_type == "Incorrect Date Ordering":
        return pd.Timestamp(value) < pd.Timestamp(row["Loss_Date"])
    if issue_type == "Future Settlement Date":
        return pd.Timestamp(value) > AS_OF_DATE
    if issue_type == "Whitespace":
        return str(value) != str(value).strip()
    if issue_type == "Mixed Capitalization":
        return str(value) not in CLAIM_TYPES and str(value).title() in CLAIM_TYPES
    if issue_type == "Invalid Claim Type":
        return str(value) not in CLAIM_TYPES
    if issue_type == "Duplicate Row":
        return int((raw["Claim_ID"] == row["Claim_ID"]).sum()) > 1
    return False


def main() -> None:
    if not RAW_FILE.exists() or not MANIFEST_FILE.exists():
        raise FileNotFoundError("Run generate_synthetic_claims.py before validation.")

    raw = pd.read_csv(RAW_FILE, dtype=str, keep_default_na=False)
    raw["_Raw_Row_ID"] = raw["_Raw_Row_ID"].astype(int)
    manifest = pd.read_csv(MANIFEST_FILE, dtype=str, keep_default_na=False)
    manifest["Raw_Row_ID"] = manifest["Raw_Row_ID"].astype(int)
    indexed = raw.set_index("_Raw_Row_ID", drop=False)

    detected: list[dict[str, str]] = []
    missed: list[str] = []
    for _, seed in manifest.iterrows():
        raw_row_id = int(seed["Raw_Row_ID"])
        if raw_row_id not in indexed.index:
            missed.append(seed["Seed_ID"])
            continue
        row = indexed.loc[raw_row_id].copy()
        row["_Issue_Value"] = row[seed["Column_Name"]]
        if _detect(seed["Issue_Type"], row, raw):
            detected.append(
                {
                    "Issue_ID": f"DQ-{len(detected) + 1:05d}",
                    "Claim_ID": seed["Claim_ID"],
                    "Issue_Type": seed["Issue_Type"],
                    "Severity": seed["Severity"],
                    "Original_Value": seed["Original_Value"],
                    "Corrected_Value": seed["Corrected_Value"],
                    "Resolution": seed["Resolution"],
                }
            )
        else:
            missed.append(seed["Seed_ID"])

    issues = pd.DataFrame(detected)
    issues.to_csv(DATA_DIR / "data_quality_issues.csv", index=False)
    summary = {
        "synthetic": True,
        "raw_rows": int(len(raw)),
        "unique_claim_ids": int(raw["Claim_ID"].nunique()),
        "seeded_issue_events": int(len(manifest)),
        "detected_issue_events": int(len(issues)),
        "detection_rate": round(len(issues) / len(manifest), 6) if len(manifest) else 1.0,
        "missed_seed_ids": missed,
        "duplicate_raw_rows": int(raw.duplicated(subset=["Claim_ID"], keep=False).sum() - raw["Claim_ID"].duplicated(keep=False).groupby(raw["Claim_ID"]).transform("max").groupby(raw["Claim_ID"]).first().sum()),
        "issues_by_type": issues["Issue_Type"].value_counts().sort_index().to_dict(),
        "issues_by_severity": issues["Severity"].value_counts().sort_index().to_dict(),
    }
    # The duplicate event count is more useful than the duplicated-members count.
    summary["duplicate_issue_events"] = int((issues["Issue_Type"] == "Duplicate Row").sum())
    (DATA_DIR / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if missed:
        raise RuntimeError(f"Validation missed {len(missed)} seeded issues: {missed[:5]}")
    print(f"Detected all {len(issues):,} seeded quality issues across {len(raw):,} raw rows.")


if __name__ == "__main__":
    main()
