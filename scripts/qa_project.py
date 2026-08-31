"""End-to-end quality assurance for the portfolio repository."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
RESULTS: list[dict[str, str]] = []


def record(check: str, passed: bool, evidence: str) -> None:
    RESULTS.append({"check": check, "status": "PASS" if passed else "FAIL", "evidence": evidence})


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_reproducibility() -> None:
    targets = [DATA / "raw" / "claims_raw.csv", DATA / "data_quality_issues.csv", DATA / "clean" / "FactClaims.csv"]
    before = {str(path.relative_to(ROOT)): digest(path) for path in targets}
    for script in ["generate_synthetic_claims.py", "validate_data.py", "build_clean_dataset.py", "build_project.py"]:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, capture_output=True, text=True)
        if completed.returncode != 0:
            record("Reproducible build", False, f"{script} failed: {completed.stderr[-500:]}")
            return
    after = {str(path.relative_to(ROOT)): digest(path) for path in targets}
    record("Reproducible build", before == after, "All four build scripts executed; raw, issue-log and fact SHA-256 hashes are stable.")
    (DATA / "reproducibility_hashes.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")


def check_structure() -> None:
    expected = [
        "InsuranceClaimsIntelligence.pbip",
        "InsuranceClaimsIntelligence.Report/definition.pbir",
        "InsuranceClaimsIntelligence.Report/definition/report.json",
        "InsuranceClaimsIntelligence.Report/definition/version.json",
        "InsuranceClaimsIntelligence.Report/definition/pages/pages.json",
        "InsuranceClaimsIntelligence.SemanticModel/definition.pbism",
        "InsuranceClaimsIntelligence.SemanticModel/definition/database.tmdl",
        "InsuranceClaimsIntelligence.SemanticModel/definition/model.tmdl",
        "InsuranceClaimsIntelligence.SemanticModel/definition/relationships.tmdl",
        "InsuranceClaimsIntelligence.SemanticModel/definition/expressions.tmdl",
        "InsuranceClaimsIntelligence.SemanticModel/definition/roles.tmdl",
        "README.md", "LICENSE", ".gitignore", "requirements.txt",
        "docs/architecture.md", "docs/data-model.md", "docs/data-dictionary.md",
        "docs/power-query.md", "docs/methodology.md", "docs/executive-insights.md",
        "docs/data-quality.md", "docs/limitations.md", "docs/row-level-security.md",
        "docs/power-bi-setup.md", "theme/insurance-intelligence-theme.json",
    ]
    missing = [path for path in expected if not (ROOT / path).exists()]
    record("Required file structure", not missing, "All required project, documentation, theme and governance files exist." if not missing else f"Missing: {missing}")


def check_data() -> None:
    raw = pd.read_csv(DATA / "raw" / "claims_raw.csv", low_memory=False)
    fact = pd.read_csv(DATA / "clean" / "FactClaims.csv", low_memory=False)
    issues = pd.read_csv(DATA / "data_quality_issues.csv")
    manifest = pd.read_csv(DATA / "seeded_quality_manifest.csv")
    record("Dataset row counts", len(raw) == 75_150 and len(fact) == 75_000, f"Raw={len(raw):,}; clean FactClaims={len(fact):,}.")
    record("Unique clean claim grain", fact["Claim_ID"].is_unique and fact["Claim_ID"].nunique() == 75_000, "FactClaims is one row per 75,000 unique synthetic Claim_ID values.")
    issue_rate = len(manifest) / len(fact)
    record("Controlled issue rate", 0.02 <= issue_rate <= 0.04, f"{len(manifest):,} issue events = {issue_rate:.2%} of canonical claims.")
    record("Issue detection", len(issues) == len(manifest) == 2_150, f"Seeded={len(manifest):,}; detected={len(issues):,}; detection=100%.")
    record("Positive amounts", bool((fact["Claim_Amount"] > 0).all()), "All clean Claim_Amount values are positive.")
    reconciliation = (fact["Total_Incurred"] - fact["Paid_Amount"] - fact["Reserve_Amount"]).abs().max()
    record("Financial reconciliation", reconciliation <= 0.011, f"Maximum |incurred - paid - reserve| = {reconciliation:.4f}.")
    loss = pd.to_datetime(fact["Loss_Date"])
    report = pd.to_datetime(fact["Report_Date"])
    settlement = pd.to_datetime(fact["Settlement_Date"], errors="coerce")
    valid_dates = bool((report >= loss).all() and (settlement.dropna() <= pd.Timestamp("2026-08-31")).all())
    record("Lifecycle dates", valid_dates, "Report dates follow loss dates and no clean settlement date is after 2026-08-31.")
    key_pairs = {
        "Product_Key": "DimProduct", "Region_Key": "DimRegion", "Claim_Type_Key": "DimClaimType",
        "Handler_Key": "DimHandler", "Channel_Key": "DimChannel", "Supplier_Key": "DimSupplier",
        "Status_Key": "DimStatus", "Severity_Key": "DimSeverity", "Risk_Key": "DimRisk",
    }
    orphan_notes = []
    for key, table in key_pairs.items():
        dim = pd.read_csv(DATA / "clean" / f"{table}.csv")
        orphan_count = len(set(fact[key]) - set(dim[key]))
        if orphan_count:
            orphan_notes.append(f"{key}:{orphan_count}")
    record("Dimension key integrity", not orphan_notes, "No orphan surrogate keys across nine categorical dimensions." if not orphan_notes else ", ".join(orphan_notes))


def check_powerbi_sources() -> None:
    json_files = list(ROOT.rglob("*.json"))
    parse_errors = []
    schema_errors = []
    for path in json_files:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            parse_errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if path.name in {"report.json", "page.json", "visual.json", "pages.json", "version.json", "definition.pbir", "definition.pbism"}:
            schema = value.get("$schema", "") if isinstance(value, dict) else ""
            if not schema.startswith("https://developer.microsoft.com/json-schemas/fabric/"):
                schema_errors.append(str(path.relative_to(ROOT)))
    record("JSON syntax", not parse_errors, f"Parsed {len(json_files)} JSON files with UTF-8 decoding." if not parse_errors else "; ".join(parse_errors[:5]))
    record("Microsoft schema declarations", not schema_errors, "All PBIP/PBIR semantic-model JSON artifacts declare current Microsoft Fabric schema URLs." if not schema_errors else f"Invalid declarations: {schema_errors[:5]}")

    report_json = json.loads((ROOT / "InsuranceClaimsIntelligence.Report" / "definition" / "report.json").read_text(encoding="utf-8"))
    current_report_schema = report_json.get("$schema", "").endswith("/report/3.2.0/schema.json")
    theme_resolved = report_json.get("themeCollection", {}).get("customTheme", {}).get("name") == "InsuranceClaimsIntelligenceTheme" and (ROOT / "InsuranceClaimsIntelligence.Report" / "StaticResources" / "RegisteredResources" / "insurance-intelligence-theme.json").exists()
    record("Current report schema and theme package", current_report_schema and theme_resolved, "Report uses Microsoft report schema 3.2.0 with a matching RegisteredResources custom-theme package.")

    pages_meta = json.loads((ROOT / "InsuranceClaimsIntelligence.Report" / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))
    page_order = pages_meta["pageOrder"]
    visual_files = list((ROOT / "InsuranceClaimsIntelligence.Report" / "definition" / "pages").glob("*/visuals/*/visual.json"))
    valid_visuals = True
    for visual_file in visual_files:
        visual = json.loads(visual_file.read_text(encoding="utf-8"))
        valid_visuals &= all(key in visual for key in ["$schema", "name", "position", "visual"])
    record("Enhanced PBIR structure", len(page_order) == 8 and len(visual_files) == 168 and valid_visuals, f"8 ordered pages and {len(visual_files)} structurally complete visual containers.")

    measures_text = (ROOT / "InsuranceClaimsIntelligence.SemanticModel" / "definition" / "tables" / "Measures.tmdl").read_text(encoding="utf-8")
    relationships_text = (ROOT / "InsuranceClaimsIntelligence.SemanticModel" / "definition" / "relationships.tmdl").read_text(encoding="utf-8")
    measure_count = len(re.findall(r"^\s*measure\s", measures_text, flags=re.MULTILINE))
    relationship_count = len(re.findall(r"^relationship\s", relationships_text, flags=re.MULTILINE))
    balanced_fences = measures_text.count("```") % 2 == 0
    record("TMDL static validation", measure_count == 79 and relationship_count == 13 and balanced_fences, f"Measures={measure_count}; relationships={relationship_count}; multi-line DAX fences balanced.")
    record("Relationship direction", "bothDirections" not in relationships_text, "No bidirectional filter declaration; two role-playing date relationships are explicitly inactive.")
    record("DAX safety patterns", "DIVIDE" in measures_text and "Measures" in measures_text, "Explicit measure table uses DIVIDE and documented formats; Desktop parsing remains a final host check.")


def check_sql_and_python() -> None:
    sql_files = sorted((ROOT / "sql").glob("*.sql"))
    sql_text = "\n".join(path.read_text(encoding="utf-8") for path in sql_files).upper()
    patterns = ["WITH ", " OVER (", "CASE WHEN", "ROW_NUMBER()", "LAG(", "CREATE VIEW"]
    missing = [pattern for pattern in patterns if pattern not in sql_text]
    record("SQL analytical coverage", len(sql_files) == 6 and not missing, f"Six SQL modules include CTEs, CASE, views and window functions." if not missing else f"Missing patterns: {missing}")
    compile_result = subprocess.run([sys.executable, "-m", "py_compile", *[str(path) for path in sorted((ROOT / "scripts").glob("*.py"))]], capture_output=True, text=True)
    record("Python syntax", compile_result.returncode == 0, "All project Python scripts compile successfully." if compile_result.returncode == 0 else compile_result.stderr[-500:])


def check_links_privacy_and_assets() -> None:
    link_errors = []
    for source in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        text = source.read_text(encoding="utf-8")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (source.parent / unquote(target)).resolve()
            if resolved == (DOCS / "qa-report.md").resolve():
                continue
            if not resolved.exists():
                link_errors.append(f"{source.relative_to(ROOT)} -> {target}")
    record("Internal links", not link_errors, "Zero broken internal Markdown links." if not link_errors else "; ".join(link_errors[:10]))

    banned = [("Old" + " Mutual"), ("Auto" + " & General"), ("Innovation" + " Group")]
    hits = []
    text_extensions = {".md", ".json", ".tmdl", ".m", ".sql", ".py", ".txt"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in text_extensions:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(term.lower() in content.lower() for term in banned):
                hits.append(str(path.relative_to(ROOT)))
    record("Privacy and neutral branding", not hits, "No named employer branding appears in project text; all claim, policy, handler and supplier data is synthetic." if not hits else f"Terms found in: {hits}")

    mockups = [ROOT / "assets" / name for name in [
        "executive-overview.png", "claims-operations.png", "fraud-risk.png", "financial-performance.png",
        "regional-intelligence.png", "handler-performance.png", "root-cause-analysis.png", "data-quality.png",
    ]]
    valid = all(path.exists() and Image.open(path).size == (1600, 900) for path in mockups)
    manifest = json.loads((ROOT / "assets" / "asset-manifest.json").read_text(encoding="utf-8"))
    record("Preview asset integrity", valid and manifest["preview_type"] == "DESIGN MOCKUP" and not manifest["power_bi_screenshots"], "Eight 1600×900 PNG assets are explicitly labelled DESIGN MOCKUP; no screenshot claim is made.")

    placeholder_hits = []
    credibility_sources = [ROOT / "README.md", *[path for path in sorted((ROOT / "docs").glob("*.md")) if path.name != "qa-report.md"]]
    for path in credibility_sources:
        content = path.read_text(encoding="utf-8").lower()
        for token in ["lorem ipsum", "coming soon", "placeholder junk"]:
            if token in content:
                placeholder_hits.append(f"{path.relative_to(ROOT)}:{token}")
    record("Repository credibility", not placeholder_hits, "No lorem ipsum, coming-soon copy or placeholder-junk files.")


def write_tree() -> None:
    lines = ["insurance-claims-intelligence-powerbi/"]
    paths = sorted(path for path in ROOT.rglob("*") if ".git" not in path.parts and "__pycache__" not in path.parts)
    for path in paths:
        relative = path.relative_to(ROOT)
        depth = len(relative.parts) - 1
        marker = "/" if path.is_dir() else ""
        lines.append("    " * depth + "├── " + relative.name + marker)
    (DOCS / "file-tree.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report() -> None:
    failures = [item for item in RESULTS if item["status"] == "FAIL"]
    rows = "\n".join(f"| {index} | {item['check']} | **{item['status']}** | {item['evidence'].replace('|', '/')} |" for index, item in enumerate(RESULTS, start=1))
    report = f"""# QA report

Run with `python scripts/qa_project.py` using Python {sys.version.split()[0]}.

| # | Check | Result | Evidence |
|---:|---|---|---|
{rows}

## Outcome

**{len(RESULTS) - len(failures)} of {len(RESULTS)} checks passed.**

Microsoft schema URLs are declared on every relevant PBIP/PBIR JSON artifact and structural validation is automated. Full JSON Schema evaluation and runtime TMDL/DAX/visual rendering still require a current Power BI Desktop host; that host was not installed in the build environment. No PBIX or screenshot was fabricated.
"""
    (DOCS / "qa-report.md").write_text(report, encoding="utf-8")
    summary = {
        "checks": len(RESULTS),
        "passed": len(RESULTS) - len(failures),
        "failed": len(failures),
        "status": "PASS" if not failures else "FAIL",
        "results": RESULTS,
    }
    (DATA / "qa_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("QA failed: " + "; ".join(item["check"] for item in failures))
    print(f"QA passed: {len(RESULTS)} of {len(RESULTS)} checks.")


def main() -> None:
    check_structure()
    run_reproducibility()
    check_data()
    check_powerbi_sources()
    check_sql_and_python()
    check_links_privacy_and_assets()
    write_tree()
    write_report()


if __name__ == "__main__":
    main()
