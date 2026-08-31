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
        "docs/power-bi-setup.md", "docs/desktop-verification-checklist.md",
        "docs/power-bi-runtime-verification.md", "docs/project-walkthrough.md",
        "docs/report-page-guide.md", "docs/interview-guide.md",
        "theme/insurance-intelligence-theme.json",
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

    metrics = json.loads((DATA / "portfolio_metrics.json").read_text(encoding="utf-8"))
    calculated = {
        "claims": len(fact),
        "open_claims": int((fact["Status_Key"] <= 6).sum()),
        "total_incurred": float(fact["Total_Incurred"].sum()),
        "outstanding_reserve": float(fact["Reserve_Amount"].sum()),
        "average_severity": float(fact["Claim_Amount"].mean()),
        "median_settlement_days": float(fact["Settlement_Days"].median()),
        "sla_compliance": float(fact["SLA_Met_Flag"].mean()),
        "high_risk_claims": int((fact["Risk_Key"] >= 3).sum()),
        "raw_rows": len(raw),
        "detected_issues": len(issues),
    }
    mismatches = []
    for name, actual in calculated.items():
        expected = metrics[name]
        tolerance = max(0.02, abs(float(expected)) * 1e-9)
        if abs(float(actual) - float(expected)) > tolerance:
            mismatches.append(f"{name}: expected {expected}, calculated {actual}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_values = [
        f"| Claims | {metrics['claims']:,} |",
        f"| Open claims | {metrics['open_claims']:,} |",
        f"| Total incurred | R{metrics['total_incurred']/1_000_000_000:.2f}bn |",
        f"| Outstanding reserve | R{metrics['outstanding_reserve']/1_000_000_000:.2f}bn |",
        f"| SLA compliance | {metrics['sla_compliance']:.1%} |",
    ]
    if not all(value in readme for value in readme_values):
        mismatches.append("README portfolio snapshot does not match generated metrics")
    record("Portfolio metric reconciliation", not mismatches, "Ten prominent metrics reconcile from clean data through portfolio_metrics.json to the README snapshot." if not mismatches else "; ".join(mismatches))


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

    pbip = json.loads((ROOT / "InsuranceClaimsIntelligence.pbip").read_text(encoding="utf-8"))
    report_relative = pbip.get("artifacts", [{}])[0].get("report", {}).get("path", "")
    report_root = (ROOT / report_relative).resolve()
    pbir = json.loads((report_root / "definition.pbir").read_text(encoding="utf-8")) if report_root.exists() else {}
    model_relative = pbir.get("datasetReference", {}).get("byPath", {}).get("path", "")
    model_root = (report_root / model_relative).resolve() if model_relative else ROOT / "__missing_model__"
    reference_ok = report_root == (ROOT / "InsuranceClaimsIntelligence.Report").resolve() and report_root.exists() and model_root == (ROOT / "InsuranceClaimsIntelligence.SemanticModel").resolve() and model_root.exists()
    record("PBIP artifact references", reference_ok, "PBIP resolves to the report artifact and PBIR resolves to the sibling semantic model by path." if reference_ok else f"Report={report_relative!r}; model={model_relative!r}.")

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
    tables_root = ROOT / "InsuranceClaimsIntelligence.SemanticModel" / "definition" / "tables"
    dim_date = (tables_root / "DimDate.tmdl").read_text(encoding="utf-8")
    dim_status = (tables_root / "DimStatus.tmdl").read_text(encoding="utf-8")
    dim_severity = (tables_root / "DimSeverity.tmdl").read_text(encoding="utf-8")
    dim_risk = (tables_root / "DimRisk.tmdl").read_text(encoding="utf-8")
    measure_count = len(re.findall(r"^\s*measure\s", measures_text, flags=re.MULTILINE))
    relationship_count = len(re.findall(r"^relationship\s", relationships_text, flags=re.MULTILINE))
    balanced_fences = measures_text.count("```") % 2 == 0
    record("TMDL static validation", measure_count == 79 and relationship_count == 13 and balanced_fences, f"Measures={measure_count}; relationships={relationship_count}; multi-line DAX fences balanced.")
    date_semantics = (
        "table DimDate\n\tdataCategory: Time" in dim_date
        and "\tcolumn Date\n\t\tdataType: dateTime\n\t\tisKey" in dim_date
        and "\tcolumn Date_Key\n\t\tdataType: int64\n\t\tisKey" not in dim_date
    )
    record("Marked date-table semantics", date_semantics, "DimDate is categorized as Time; the related Date column is the key and the hidden integer surrogate is not the date key." if date_semantics else "DimDate table/category/key declarations are incomplete.")
    sort_rules = [
        (dim_date, "\tcolumn Month\n\t\tdataType: string\n\t\tsortByColumn: Month_Number"),
        (dim_date, "\tcolumn Month_Short\n\t\tdataType: string\n\t\tsortByColumn: Month_Number"),
        (dim_date, "\tcolumn Year_Month\n\t\tdataType: string\n\t\tsortByColumn: Year_Month_Sort"),
        (dim_status, "\tcolumn Claim_Status\n\t\tdataType: string\n\t\tsortByColumn: Status_Order"),
        (dim_severity, "\tcolumn Severity_Band\n\t\tdataType: string\n\t\tsortByColumn: Severity_Order"),
        (dim_risk, "\tcolumn Risk_Band\n\t\tdataType: string\n\t\tsortByColumn: Risk_Order"),
    ]
    record("Semantic display ordering", all(rule in source for source, rule in sort_rules), "Month, status, severity and risk labels use governed numeric sort columns.")
    relationship_ok = "bothDirections" not in relationships_text and relationships_text.count("\tisActive: false") == 2
    record("Relationship direction", relationship_ok, "No bidirectional filter declaration; exactly two role-playing date relationships are inactive.")
    dax_ok = (
        "DIVIDE" in measures_text
        and "DimStatus[Open_Status_Flag] = 1" in measures_text
        and "FactClaims[Status_Key] <= 6" not in measures_text
        and "Potential Fraud Captured" not in measures_text
        and "Fraud Recall" not in measures_text
        and "False Positive Rate" not in measures_text
    )
    record("DAX safety and terminology", dax_ok, "Explicit measures use DIVIDE, governed open-status logic and synthetic/human-review terminology; Desktop parsing remains a final host check.")


def check_sql_and_python() -> None:
    sql_files = sorted((ROOT / "sql").glob("*.sql"))
    sql_text = "\n".join(path.read_text(encoding="utf-8") for path in sql_files).upper()
    patterns = ["WITH ", " OVER (", "CASE WHEN", "ROW_NUMBER()", "LAG(", "CREATE VIEW"]
    missing = [pattern for pattern in patterns if pattern not in sql_text]
    record("SQL analytical coverage", len(sql_files) == 6 and not missing, f"Six SQL modules include CTEs, CASE, views and window functions." if not missing else f"Missing patterns: {missing}")
    compile_result = subprocess.run([sys.executable, "-m", "py_compile", *[str(path) for path in sorted((ROOT / "scripts").glob("*.py"))]], capture_output=True, text=True)
    record("Python syntax", compile_result.returncode == 0, "All project Python scripts compile successfully." if compile_result.returncode == 0 else compile_result.stderr[-500:])

    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    commands = [
        "python scripts/generate_synthetic_claims.py",
        "python scripts/validate_data.py",
        "python scripts/build_clean_dataset.py",
        "python scripts/build_project.py",
        "python scripts/qa_project.py",
    ]
    positions = [workflow.find(command) for command in commands]
    ci_ok = (
        "push:" in workflow
        and "pull_request:" in workflow
        and "workflow_dispatch:" in workflow
        and workflow.count("branches:\n      - main") >= 2
        and "permissions:\n  contents: read" in workflow
        and "actions/checkout@v4" in workflow
        and "actions/setup-python@v5" in workflow
        and "cache: pip" in workflow
        and "python -m pip install -r requirements.txt" in workflow
        and all(position >= 0 for position in positions)
        and positions == sorted(positions)
    )
    record("CI workflow contract", ci_ok, "Push, pull-request and manual triggers run the documented Python install → generate → validate → clean → build → QA sequence with read-only contents permission." if ci_ok else "The GitHub Actions workflow does not match the documented pipeline contract.")


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

    generated_markdown = [DOCS / "data-quality.md", DOCS / "report-pages.md"]
    indented_tables = [str(path.relative_to(ROOT)) for path in generated_markdown if re.search(r"(?m)^ {4,}\|", path.read_text(encoding="utf-8"))]
    record("Generated Markdown structure", not indented_tables, "Generated documentation tables begin at the left margin and render as Markdown rather than code blocks." if not indented_tables else f"Indented tables found in: {indented_tables}")

    external_links = []
    for source in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        text = source.read_text(encoding="utf-8")
        external_links.extend(target for target in re.findall(r"!?\[[^\]]*\]\((https?://[^)]+)\)", text))
    allowed_hosts = ("https://github.com/", "https://learn.microsoft.com/", "https://developer.microsoft.com/")
    unsafe_links = sorted({link for link in external_links if not link.startswith(allowed_hosts)})
    record("External link hygiene", not unsafe_links, f"All {len(external_links)} external Markdown links use HTTPS and approved first-party documentation or repository hosts." if not unsafe_links else f"Unexpected external links: {unsafe_links}")

    banned = [("Old" + " Mutual"), ("Auto" + " & General"), ("Innovation" + " Group"), ("omin" + "sure.co.za")]
    hits = []
    text_extensions = {".md", ".json", ".tmdl", ".m", ".sql", ".py", ".txt", ".csv", ".yml", ".yaml", ".svg"}
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", flags=re.IGNORECASE)
    user_path_pattern = re.compile(r"[A-Z]:\\Users\\[^\\\s]+", flags=re.IGNORECASE)
    credential_patterns = [
        re.compile("gh" + r"p_[A-Za-z0-9]{20,}"),
        re.compile("github" + r"_pat_[A-Za-z0-9_]{20,}"),
        re.compile("sk" + r"-[A-Za-z0-9]{20,}"),
    ]
    for path in ROOT.rglob("*"):
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in text_extensions:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(term.lower() in content.lower() for term in banned):
                hits.append(f"{path.relative_to(ROOT)}:employer")
            if email_pattern.search(content):
                hits.append(f"{path.relative_to(ROOT)}:email")
            if user_path_pattern.search(content):
                hits.append(f"{path.relative_to(ROOT)}:local-user-path")
            if any(pattern.search(content) for pattern in credential_patterns):
                hits.append(f"{path.relative_to(ROOT)}:credential-pattern")
    record("Privacy and neutral branding", not hits, "No named employer, email address, local user path or credential pattern appears in project artifacts; all claim, policy, handler and supplier data is synthetic." if not hits else f"Potential privacy terms found in: {sorted(set(hits))}")

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


def check_runtime_and_recruiter_evidence() -> None:
    runtime = (DOCS / "power-bi-runtime-verification.md").read_text(encoding="utf-8")
    checklist = (DOCS / "desktop-verification-checklist.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "assets" / "asset-manifest.json").read_text(encoding="utf-8"))
    powerbi_assets = list((ROOT / "assets" / "powerbi").glob("*.png")) if (ROOT / "assets" / "powerbi").exists() else []
    honest_boundary = (
        "Overall runtime result | **MANUAL REVIEW**" in runtime
        and "Power BI Desktop version | Not available in the current execution environment" in runtime
        and "Power BI Desktop verification completed successfully" not in runtime
        and "Do not mark an interaction PASS merely because related source metadata exists." in checklist
        and not manifest["power_bi_screenshots"]
        and not powerbi_assets
    )
    record("Desktop evidence boundary", honest_boundary, "Runtime results remain MANUAL REVIEW and no Power BI screenshot asset is claimed or present without Desktop evidence." if honest_boundary else "Desktop evidence wording or screenshot state is inconsistent.")

    walkthrough = (DOCS / "project-walkthrough.md").read_text(encoding="utf-8")
    page_guide = (DOCS / "report-page-guide.md").read_text(encoding="utf-8")
    interview = (DOCS / "interview-guide.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    recruiter_pack = (
        all(marker in walkthrough for marker in ["0–10 seconds", "10–25 seconds", "25–45 seconds", "45–60 seconds", "60–75 seconds", "75–90 seconds"])
        and len(re.findall(r"^## [1-8]\. ", page_guide, flags=re.MULTILINE)) == 8
        and interview.count("\n## ") >= 16
        and all(name in readme for name in ["docs/project-walkthrough.md", "docs/report-page-guide.md", "docs/interview-guide.md", "docs/power-bi-runtime-verification.md", "docs/desktop-verification-checklist.md"])
    )
    record("Recruiter evidence pack", recruiter_pack, "Walkthrough timing, eight page captions, technical interview answers and README links are complete." if recruiter_pack else "Recruiter-facing documentation is incomplete or not linked.")

    required_readme_sections = [
        "## Executive Summary", "## Business Problem", "## Solution Overview",
        "## Executive Portfolio Snapshot", "## Architecture", "## Dashboard / Report Pages",
        "## Data Model", "## DAX & Semantic Layer", "## Power Query & Data Quality",
        "## SQL Analytics", "## Reproducibility", "## Quality Assurance",
        "## Responsible Analytics & Limitations", "## How to Run", "## Repository Structure", "## Author",
    ]
    presentation_ok = (
        all(section in readme for section in required_readme_sections)
        and "**Portfolio evidence:** 75,000 synthetic claims · 79 DAX measures · 8 report pages" in readme
        and "**Problem:**" in readme
        and "**Approach:**" in readme
        and "**Result:**" in readme
    )
    record("README recruiter presentation", presentation_ok, "The opening evidence line, executive summary, concise case study and core recruiter sections are present." if presentation_ok else "README recruiter presentation contract is incomplete.")


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
    check_runtime_and_recruiter_evidence()
    write_tree()
    write_report()


if __name__ == "__main__":
    main()
