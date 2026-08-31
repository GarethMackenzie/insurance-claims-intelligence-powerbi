"""Build the editable PBIP/PBIR/TMDL solution and its portfolio documentation.

This script is intentionally deterministic. It consumes only the generated clean
CSV extracts and creates text-based Power BI project sources, SQL, documentation,
theme files, diagrams, and clearly labelled design mockups.
"""

from __future__ import annotations

import json
import re
import textwrap
import uuid
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CLEAN = DATA / "clean"
MODEL = ROOT / "InsuranceClaimsIntelligence.SemanticModel"
REPORT = ROOT / "InsuranceClaimsIntelligence.Report"
MODEL_DEF = MODEL / "definition"
REPORT_DEF = REPORT / "definition"
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
SQL = ROOT / "sql"
POWERQUERY = ROOT / "powerquery"
THEME = ROOT / "theme"
DAX = ROOT / "dax"

COLORS = {
    "deep_navy": "#0A1622",
    "navy": "#0F1E30",
    "slate": "#132840",
    "teal": "#2EC4B6",
    "blue": "#3F7CAC",
    "amber": "#F4A261",
    "coral": "#E8654F",
    "light": "#EAF2F8",
    "muted": "#7E93A8",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def stable_guid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"insurance-claims-intelligence/{name}"))


def measure(name: str, expression: str, fmt: str = "#,0", description: str = "", category: str = "Core") -> dict:
    return {"name": name, "expression": expression.strip(), "format": fmt, "description": description, "category": category}


def build_measures(metrics: dict) -> list[dict]:
    currency = "R #,##0;[Red]-R #,##0;R 0"
    decimal_currency = "R #,##0.00;[Red]-R #,##0.00;R 0.00"
    pct = "0.0%"
    pp = "0.0 pp"
    measures = [
        measure("Total Claims", "DISTINCTCOUNT ( FactClaims[Claim_ID] )", "#,0", "Distinct synthetic claims in filter context.", "Volume"),
        measure("Open Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ) )", "#,0", "Claims in governed open lifecycle statuses.", "Volume"),
        measure("Settled Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 7 ) )", "#,0", "Claims in Settled status.", "Volume"),
        measure("Rejected Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 8 ) )", "#,0", "Claims in Rejected status.", "Volume"),
        measure("Claims per Policy", "DIVIDE ( [Total Claims], DISTINCTCOUNT ( FactClaims[Policy_ID] ) )", "0.00", "Claim frequency proxy for the synthetic portfolio.", "Volume"),
        measure("Total Claim Amount", "SUM ( FactClaims[Claim_Amount] )", currency, "Gross synthetic claimed amount.", "Financial"),
        measure("Total Approved", "SUM ( FactClaims[Approved_Amount] )", currency, "Approved synthetic amount.", "Financial"),
        measure("Total Paid", "SUM ( FactClaims[Paid_Amount] )", currency, "Paid synthetic amount.", "Financial"),
        measure("Outstanding Reserve", "SUM ( FactClaims[Reserve_Amount] )", currency, "Outstanding simplified case reserve.", "Financial"),
        measure("Total Incurred", "SUM ( FactClaims[Total_Incurred] )", currency, "Paid plus outstanding reserve; not an actuarial estimate.", "Financial"),
        measure("Average Severity", "AVERAGE ( FactClaims[Claim_Amount] )", decimal_currency, "Mean synthetic claim amount.", "Severity"),
        measure("Median Severity", "MEDIAN ( FactClaims[Claim_Amount] )", currency, "Median synthetic claim amount.", "Severity"),
        measure("P90 Severity", "PERCENTILEX.INC ( FactClaims, FactClaims[Claim_Amount], 0.9 )", currency, "90th percentile synthetic claim amount.", "Severity"),
        measure("Average Settlement Days", "AVERAGE ( FactClaims[Settlement_Days] )", "0.0", "Average reporting-to-settlement days for settled claims.", "Operations"),
        measure("Median Settlement Days", "MEDIAN ( FactClaims[Settlement_Days] )", "0", "Median reporting-to-settlement days.", "Operations"),
        measure("90th Percentile Settlement Days", "PERCENTILEX.INC ( FILTER ( FactClaims, NOT ISBLANK ( FactClaims[Settlement_Days] ) ), FactClaims[Settlement_Days], 0.9 )", "0", "90th percentile reporting-to-settlement days.", "Operations"),
        measure("SLA Compliance %", "DIVIDE ( SUM ( FactClaims[SLA_Met_Flag] ), [Total Claims] )", pct, "Share of claims within the simulated complexity-based SLA.", "Service"),
        measure("Reopen Rate %", "DIVIDE ( SUM ( FactClaims[Reopened_Flag] ), [Total Claims] )", pct, "Share of claims marked reopened.", "Quality"),
        measure("Complaint Rate %", "DIVIDE ( SUM ( FactClaims[Complaint_Flag] ), [Total Claims] )", pct, "Share of claims with a simulated complaint flag.", "Quality"),
        measure("Fraud Referral Rate %", "DIVIDE ( SUM ( FactClaims[Fraud_Referral_Flag] ), [Total Claims] )", pct, "Share referred for review; referral does not determine fraud.", "Risk"),
        measure("High Risk Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Risk_Key] >= 3 ) )", "#,0", "Claims in High or Critical synthetic risk bands.", "Risk"),
        measure("High Risk Claims %", "DIVIDE ( [High Risk Claims], [Total Claims] )", pct, "High/Critical risk share.", "Risk"),
        measure("Active Handlers", "DISTINCTCOUNT ( FactClaims[Handler_Key] )", "#,0", "Handlers represented by filtered claims.", "Workload"),
        measure("Claims Per Handler", "DIVIDE ( [Total Claims], [Active Handlers] )", "0.0", "Filtered claims per active handler.", "Workload"),
        measure("Open Claims Per Handler", "DIVIDE ( [Open Claims], [Active Handlers] )", "0.0", "Open filtered workload per active handler.", "Workload"),
        measure("Average Reporting Delay", "AVERAGE ( FactClaims[Reporting_Delay_Days] )", "0.0", "Average days from loss to report.", "Operations"),
        measure("Average Open Age", "CALCULATE ( AVERAGE ( FactClaims[Open_Claim_Age_Days] ), KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ) )", "0.0", "Average age of claims in governed open lifecycle statuses.", "Operations"),
        measure("Claims MTD", "CALCULATE ( [Total Claims], DATESMTD ( DimDate[Date] ) )", "#,0", "Month-to-date claims by loss date.", "Time Intelligence"),
        measure("Claims QTD", "CALCULATE ( [Total Claims], DATESQTD ( DimDate[Date] ) )", "#,0", "Quarter-to-date claims by loss date.", "Time Intelligence"),
        measure("Claims YTD", "CALCULATE ( [Total Claims], DATESYTD ( DimDate[Date] ) )", "#,0", "Year-to-date claims by loss date.", "Time Intelligence"),
        measure("Claims PY", "CALCULATE ( [Total Claims], DATEADD ( DimDate[Date], -1, YEAR ) )", "#,0", "Claims in the prior-year comparison period.", "Time Intelligence"),
        measure("Claims YoY %", "VAR CurrentValue = [Total Claims]\nVAR PriorValue = [Claims PY]\nRETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )", pct, "Year-over-year claims-volume change.", "Time Intelligence"),
        measure("Incurred MTD", "CALCULATE ( [Total Incurred], DATESMTD ( DimDate[Date] ) )", currency, "Month-to-date incurred.", "Time Intelligence"),
        measure("Incurred YTD", "CALCULATE ( [Total Incurred], DATESYTD ( DimDate[Date] ) )", currency, "Year-to-date incurred.", "Time Intelligence"),
        measure("Incurred PY", "CALCULATE ( [Total Incurred], DATEADD ( DimDate[Date], -1, YEAR ) )", currency, "Prior-year incurred comparison.", "Time Intelligence"),
        measure("Incurred YoY %", "VAR CurrentValue = [Total Incurred]\nVAR PriorValue = [Incurred PY]\nRETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )", pct, "Year-over-year incurred change.", "Time Intelligence"),
        measure("Severity PY", "CALCULATE ( [Average Severity], DATEADD ( DimDate[Date], -1, YEAR ) )", currency, "Prior-year average severity.", "Time Intelligence"),
        measure("Severity YoY %", "VAR CurrentValue = [Average Severity]\nVAR PriorValue = [Severity PY]\nRETURN DIVIDE ( CurrentValue - PriorValue, PriorValue )", pct, "Year-over-year average severity change.", "Time Intelligence"),
        measure("SLA Compliance PY", "CALCULATE ( [SLA Compliance %], DATEADD ( DimDate[Date], -1, YEAR ) )", pct, "Prior-year SLA compliance.", "Time Intelligence"),
        measure("SLA Variance vs PY", "100 * ( [SLA Compliance %] - [SLA Compliance PY] )", pp, "Percentage-point SLA change versus prior year.", "Time Intelligence"),
        measure("Rolling 12M Claims", "CALCULATE ( [Total Claims], DATESINPERIOD ( DimDate[Date], MAX ( DimDate[Date] ), -12, MONTH ) )", "#,0", "Claims over the rolling 12 months ending in context.", "Time Intelligence"),
        measure("Rolling 12M Incurred", "CALCULATE ( [Total Incurred], DATESINPERIOD ( DimDate[Date], MAX ( DimDate[Date] ), -12, MONTH ) )", currency, "Incurred over the rolling 12 months ending in context.", "Time Intelligence"),
        measure("Large Loss Count", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Claim_Amount] >= 250000 ) )", "#,0", "Claims at or above R250,000.", "Financial"),
        measure("Large Loss Exposure", "CALCULATE ( [Total Incurred], KEEPFILTERS ( FactClaims[Claim_Amount] >= 250000 ) )", currency, "Incurred exposure from large losses.", "Financial"),
        measure("30+ Day Open Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ), KEEPFILTERS ( FactClaims[Open_Claim_Age_Days] >= 30 ) )", "#,0", "Open claims aged at least 30 days.", "Backlog"),
        measure("60+ Day Open Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( DimStatus[Open_Status_Flag] = 1 ), KEEPFILTERS ( FactClaims[Open_Claim_Age_Days] >= 60 ) )", "#,0", "Open claims aged at least 60 days.", "Backlog"),
        measure("Backlog %", "DIVIDE ( [30+ Day Open Claims], [Open Claims] )", pct, "Share of open claims aged at least 30 days.", "Backlog"),
        measure("Awaiting Documents Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 3 ) )", "#,0", "Claims awaiting documentation.", "Backlog"),
        measure("Awaiting Supplier Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 4 ) )", "#,0", "Claims awaiting supplier activity.", "Backlog"),
        measure("Under Investigation Claims", "CALCULATE ( [Total Claims], KEEPFILTERS ( FactClaims[Status_Key] = 5 ) )", "#,0", "Claims in the investigation queue.", "Risk"),
        measure("Reserve per Open Claim", "DIVIDE ( [Outstanding Reserve], [Open Claims] )", currency, "Outstanding reserve per open claim.", "Financial"),
        measure("Investigation Capacity %", "DIVIDE ( SELECTEDVALUE ( 'Investigation Capacity'[Investigation Capacity], 10 ), 100 )", pct, "Selected proportion of claims that the review team can investigate.", "Review Capacity"),
        measure("Claims Selected for Review", "VAR Capacity = [Investigation Capacity %]\nRETURN COUNTROWS ( FILTER ( VALUES ( FactClaims[Claim_ID] ), CALCULATE ( MAX ( FactClaims[Risk_Rank_Percentile] ) ) > 1 - Capacity ) )", "#,0", "Claims in the highest risk-score percentile within selected capacity.", "Review Capacity"),
        measure("Synthetic Targets Captured", "VAR Capacity = [Investigation Capacity %]\nRETURN SUMX ( FILTER ( VALUES ( FactClaims[Claim_ID] ), CALCULATE ( MAX ( FactClaims[Risk_Rank_Percentile] ) ) > 1 - Capacity ), CALCULATE ( MAX ( FactClaims[Synthetic_Fraud_Target_Flag] ) ) )", "#,0", "Synthetic demonstration target events in the selected review queue.", "Review Capacity"),
        measure("Synthetic Target Events", "SUM ( FactClaims[Synthetic_Fraud_Target_Flag] )", "#,0", "Synthetic binary target used only to demonstrate prioritization metrics.", "Review Capacity"),
        measure("Review Precision", "DIVIDE ( [Synthetic Targets Captured], [Claims Selected for Review] )", pct, "Synthetic target events divided by selected claims.", "Review Capacity"),
        measure("Synthetic Target Recall", "DIVIDE ( [Synthetic Targets Captured], [Synthetic Target Events] )", pct, "Share of synthetic demonstration target events captured by the queue.", "Review Capacity"),
        measure("Non-Target Review Rate", "1 - [Review Precision]", pct, "Selected claims without the synthetic target flag; this is not a real false-positive rate.", "Review Capacity"),
        measure("Review Workload", "[Claims Selected for Review]", "#,0", "Selected investigation queue volume.", "Review Capacity"),
        measure("Base Synthetic Target Rate", "DIVIDE ( [Synthetic Target Events], [Total Claims] )", pct, "Portfolio-wide synthetic target rate.", "Review Capacity"),
        measure("Lift vs Random Review", "DIVIDE ( [Review Precision], [Base Synthetic Target Rate] )", "0.00×", "Review precision divided by the portfolio target rate.", "Review Capacity"),
        measure("Detected Data Quality Issues", "COUNTROWS ( DataQualityIssues )", "#,0", "Detected raw-data issue events.", "Data Quality"),
        measure("Invalid Row Count", "DISTINCTCOUNT ( DataQualityIssues[Claim_ID] )", "#,0", "Distinct claims affected by a detected raw-data issue.", "Data Quality"),
        measure("Raw Rows", str(int(metrics["raw_rows"])), "#,0", "Rows in the generated raw extract, including controlled duplicates.", "Data Quality"),
        measure("Duplicate Rate", "DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] = \"Duplicate Row\" ), [Raw Rows] )", pct, "Duplicate issue events divided by raw rows.", "Data Quality"),
        measure("Missing Region %", "DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] = \"Missing Region\" ), [Raw Rows] )", pct, "Missing-region issue events divided by raw rows.", "Data Quality"),
        measure("Invalid Amount Count", "CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { \"Missing Claim Amount\", \"Negative Claim Amount\" } )", "#,0", "Missing or negative claim-amount issues.", "Data Quality"),
        measure("Invalid Date Count", "CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { \"Incorrect Date Ordering\", \"Future Settlement Date\" } )", "#,0", "Invalid ordering or future-date issue events.", "Data Quality"),
        measure("Completeness %", "1 - DIVIDE ( CALCULATE ( [Detected Data Quality Issues], DataQualityIssues[Issue_Type] IN { \"Missing Region\", \"Missing Claim Amount\", \"Blank Channel\" } ), [Raw Rows] * 3 )", pct, "Completeness across three controlled required fields in the raw data.", "Data Quality"),
        measure("Data Quality Score", "1 - DIVIDE ( [Detected Data Quality Issues], [Raw Rows] )", pct, "Simple transparent quality index: one minus detected issue events per raw row.", "Data Quality"),
        measure("Handler Throughput Index", "DIVIDE ( [Claims Per Handler], CALCULATE ( [Claims Per Handler], ALL ( DimHandler ) ) )", "0.00", "Relative throughput component; not a productivity judgement.", "Handler Scorecard"),
        measure("Handler Service Index", "DIVIDE ( [SLA Compliance %], CALCULATE ( [SLA Compliance %], ALL ( DimHandler ) ) )", "0.00", "Relative service component.", "Handler Scorecard"),
        measure("Handler Quality Index", "DIVIDE ( 1 - [Reopen Rate %] - [Complaint Rate %], CALCULATE ( 1 - [Reopen Rate %] - [Complaint Rate %], ALL ( DimHandler ) ) )", "0.00", "Relative quality component combining reopen and complaint signals.", "Handler Scorecard"),
        measure("Handler Complexity Index", "DIVIDE ( AVERAGE ( FactClaims[Claim_Amount] ), CALCULATE ( [Average Severity], ALL ( DimHandler ) ) )", "0.00", "Claim-value mix proxy for complexity; not a complete case-mix adjustment.", "Handler Scorecard"),
        measure("Balanced Effectiveness Score", "VAR Throughput = MIN ( [Handler Throughput Index], 1.5 )\nVAR Service = MIN ( [Handler Service Index], 1.5 )\nVAR Quality = MIN ( [Handler Quality Index], 1.5 )\nVAR Complexity = MIN ( [Handler Complexity Index], 1.5 )\nRETURN 0.25 * Throughput + 0.35 * Service + 0.25 * Quality + 0.15 * Complexity", "0.00", "Balanced workload-management demonstration; not an employee performance score.", "Handler Scorecard"),
        measure("Executive Attention — Severity", "VAR Delta = [Severity YoY %]\nRETURN IF ( ISBLANK ( Delta ), \"Severity comparison unavailable\", IF ( Delta >= 0, \"▲ Severity \" & FORMAT ( Delta, \"0.0%\" ) & \" YoY\", \"▼ Severity \" & FORMAT ( ABS ( Delta ), \"0.0%\" ) & \" YoY\" ) )", "General", "Dynamic executive exception statement.", "Executive Attention"),
        measure("Executive Attention — SLA", "VAR Delta = [SLA Variance vs PY]\nRETURN IF ( ISBLANK ( Delta ), \"SLA comparison unavailable\", IF ( Delta >= 0, \"▲ SLA compliance +\" & FORMAT ( Delta, \"0.0\" ) & \" pp\", \"▼ SLA compliance \" & FORMAT ( Delta, \"0.0\" ) & \" pp\" ) )", "General", "Dynamic SLA exception statement.", "Executive Attention"),
        measure("Executive Attention — Backlog", "\"▲ 30+ day backlog: \" & FORMAT ( [30+ Day Open Claims], \"#,0\" ) & \" claims (\" & FORMAT ( [Backlog %], \"0.0%\" ) & \")\"", "General", "Dynamic backlog exception statement.", "Executive Attention"),
        measure("Selected Metric Value", "SWITCH ( SELECTEDVALUE ( 'Analysis Metric'[Analysis Metric], \"Total Incurred\" ), \"Total Incurred\", [Total Incurred], \"Average Severity\", [Average Severity], \"Settlement Days\", [Average Settlement Days], \"SLA Compliance\", [SLA Compliance %], \"Fraud Referral Rate\", [Fraud Referral Rate %], [Total Incurred] )", "#,0.00", "Metric selector used by root-cause and comparative visuals.", "Field Parameter"),
    ]
    return measures


def dax_literal(expression: str) -> str:
    if "\n" not in expression:
        return expression
    return "```\n" + textwrap.indent(expression, "\t\t") + "\n\t```"


def create_foundation(metrics: dict) -> None:
    for path in [MODEL_DEF / "tables", REPORT_DEF / "pages", ASSETS, DOCS, SQL, POWERQUERY, THEME, DAX]:
        path.mkdir(parents=True, exist_ok=True)

    write_json(
        ROOT / "InsuranceClaimsIntelligence.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": "InsuranceClaimsIntelligence.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write_json(
        REPORT / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../InsuranceClaimsIntelligence.SemanticModel"}},
        },
    )
    write_json(
        MODEL / "definition.pbism",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.2",
            "settings": {"qnaEnabled": True},
        },
    )
    write_json(
        REPORT_DEF / "version.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0",
        },
    )
    write_json(
        REPORT_DEF / "report.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json",
            "themeCollection": {
                "customTheme": {
                    "name": "InsuranceClaimsIntelligenceTheme",
                    "reportVersionAtImport": {"visual": "2.9.0", "report": "3.2.0", "page": "2.1.0"},
                    "type": "RegisteredResources",
                }
            },
            "filterConfig": {"filters": []},
            "resourcePackages": [
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [
                        {
                            "name": "InsuranceClaimsIntelligenceTheme",
                            "path": "insurance-intelligence-theme.json",
                            "type": "CustomTheme",
                        }
                    ],
                }
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultFilterActionIsDataFilter": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "allowInlineExploration": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
            },
            "slowDataSourceSettings": {
                "isCrossHighlightingDisabled": False,
                "isSlicerSelectionsButtonEnabled": False,
                "isFilterSelectionsButtonEnabled": False,
                "isFieldWellButtonEnabled": False,
                "isApplyAllButtonEnabled": False,
            },
        },
    )
    theme = {
        "name": "Insurance Claims Intelligence",
        "dataColors": [COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["coral"], "#5E81AC", "#88C0D0"],
        "background": COLORS["deep_navy"],
        "foreground": COLORS["light"],
        "tableAccent": COLORS["teal"],
        "good": COLORS["teal"],
        "neutral": COLORS["amber"],
        "bad": COLORS["coral"],
        "textClasses": {
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 15, "color": COLORS["light"]},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": COLORS["light"]},
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": COLORS["muted"]},
            "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 24, "color": COLORS["light"]},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [{"color": {"solid": {"color": COLORS["slate"]}}, "transparency": 2}],
                    "border": [{"show": True, "color": {"solid": {"color": "#254763"}}, "radius": 8}],
                    "title": [{"show": True, "fontFace": "Segoe UI Semibold", "fontSize": 11, "fontColor": {"solid": {"color": COLORS["light"]}}}],
                    "visualHeader": [{"show": True, "foreground": {"solid": {"color": COLORS["muted"]}}}],
                }
            },
            "page": {"*": {"background": [{"color": {"solid": {"color": COLORS["deep_navy"]}}, "transparency": 0}]}}
        },
    }
    write_json(THEME / "insurance-intelligence-theme.json", theme)
    write_json(REPORT / "StaticResources" / "RegisteredResources" / "insurance-intelligence-theme.json", theme)
    write(ROOT / "requirements.txt", """
        pandas>=2.2,<3.0
        numpy>=2.0,<3.0
        Pillow>=10.0,<13.0
    """)
    write(ROOT / ".gitignore", """
        # Power BI Desktop local caches
        **/.pbi/localSettings.json
        **/.pbi/cache.abf
        **/.pbi/*.lock
        **/.pbi/desktop.json

        # Python
        __pycache__/
        *.py[cod]
        .venv/
        venv/
        .pytest_cache/

        # Editors and operating systems
        .idea/
        .vscode/
        .DS_Store
        Thumbs.db
        *.tmp
        *.bak

        # Credentials and local configuration
        .env
        .env.*
        *.secret
        *.credentials
    """)
    write(ROOT / "LICENSE", """
        MIT License

        Copyright (c) 2026 Gareth Andrew Mackenzie

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
    """)


TYPE_OVERRIDES = {
    "Loss_Date": "dateTime", "Report_Date": "dateTime", "Assignment_Date": "dateTime",
    "Assessment_Date": "dateTime", "Decision_Date": "dateTime", "Settlement_Date": "dateTime",
    "Date": "dateTime", "Latitude": "double", "Longitude": "double",
    "Claim_Amount": "decimal", "Approved_Amount": "decimal", "Paid_Amount": "decimal",
    "Reserve_Amount": "decimal", "Total_Incurred": "decimal", "Fraud_Risk_Score": "double",
    "Risk_Rank_Percentile": "double", "Settlement_Days": "double",
}


def infer_tmdl_type(column: str, dtype) -> str:
    if column in TYPE_OVERRIDES:
        return TYPE_OVERRIDES[column]
    if pd.api.types.is_integer_dtype(dtype):
        return "int64"
    if pd.api.types.is_float_dtype(dtype):
        return "double"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    return "string"


def m_type(tmdl_type: str) -> str:
    return {"int64": "Int64.Type", "double": "type number", "decimal": "Currency.Type", "boolean": "type logical", "dateTime": "type date", "string": "type text"}[tmdl_type]


def quote_tmdl(name: str) -> str:
    return f"'{name}'" if any(ch in name for ch in " -+%&/") else name


def table_tmdl(
    table_name: str,
    csv_path: Path,
    key_columns: set[str] | None = None,
    hidden_columns: set[str] | None = None,
    table_data_category: str | None = None,
    sort_columns: dict[str, str] | None = None,
) -> str:
    key_columns = key_columns or set()
    hidden_columns = hidden_columns or set()
    sort_columns = sort_columns or {}
    frame = pd.read_csv(csv_path, nrows=200)
    lines = [f"table {quote_tmdl(table_name)}"]
    if table_data_category:
        lines.append(f"\tdataCategory: {table_data_category}")
    m_fields = []
    for column in frame.columns:
        dtype = infer_tmdl_type(column, frame[column].dtype)
        lines.append(f"\tcolumn {quote_tmdl(column)}")
        lines.append(f"\t\tdataType: {dtype}")
        if column in key_columns:
            lines.append("\t\tisKey")
        if column in hidden_columns:
            lines.append("\t\tisHidden")
        if column in sort_columns:
            lines.append(f"\t\tsortByColumn: {quote_tmdl(sort_columns[column])}")
        if dtype in {"int64", "double", "decimal"}:
            lines.append("\t\tsummarizeBy: none")
        if dtype == "dateTime":
            lines.append("\t\tformatString: yyyy-MM-dd")
        if dtype == "decimal":
            lines.append("\t\tformatString: R #,##0.00;[Red]-R #,##0.00;R 0.00")
        if column == "Region":
            lines.append("\t\tdataCategory: StateOrProvince")
        elif column == "Latitude":
            lines.append("\t\tdataCategory: Latitude")
        elif column == "Longitude":
            lines.append("\t\tdataCategory: Longitude")
        lines.append(f"\t\tsourceColumn: {column}")
        m_fields.append(f"{column} = {m_type(dtype)}")
    relative = csv_path.relative_to(ROOT).as_posix().replace("/", "\\")
    lines.extend(
        [
            "",
            f"\tpartition {quote_tmdl(table_name)} = m",
            "\t\tmode: import",
            "\t\tsource =",
            f"\t\t\tfnLoadCsv(\"{relative}\", type table [{', '.join(m_fields)}])",
            "",
            "\tannotation PBI_ResultType = Table",
        ]
    )
    return "\n".join(lines) + "\n"


def create_semantic_model(measures: list[dict]) -> int:
    tables = [
        ("DimDate", CLEAN / "DimDate.csv", {"Date"}, "Time", {"Month": "Month_Number", "Month_Short": "Month_Number", "Year_Month": "Year_Month_Sort"}),
        ("DimProduct", CLEAN / "DimProduct.csv", {"Product_Key"}, None, {}),
        ("DimRegion", CLEAN / "DimRegion.csv", {"Region_Key"}, None, {}),
        ("DimClaimType", CLEAN / "DimClaimType.csv", {"Claim_Type_Key"}, None, {}),
        ("DimHandler", CLEAN / "DimHandler.csv", {"Handler_Key"}, None, {}),
        ("DimChannel", CLEAN / "DimChannel.csv", {"Channel_Key"}, None, {}),
        ("DimSupplier", CLEAN / "DimSupplier.csv", {"Supplier_Key"}, None, {}),
        ("DimStatus", CLEAN / "DimStatus.csv", {"Status_Key"}, None, {"Claim_Status": "Status_Order"}),
        ("DimSeverity", CLEAN / "DimSeverity.csv", {"Severity_Key"}, None, {"Severity_Band": "Severity_Order"}),
        ("DimRisk", CLEAN / "DimRisk.csv", {"Risk_Key"}, None, {"Risk_Band": "Risk_Order"}),
        ("FactClaims", CLEAN / "FactClaims.csv", {"Claim_ID"}, None, {}),
        ("DataQualityIssues", DATA / "data_quality_issues.csv", {"Issue_ID"}, None, {}),
    ]
    hidden_fact = {
        "Loss_Date_Key", "Report_Date_Key", "Settlement_Date_Key", "Product_Key", "Region_Key",
        "Claim_Type_Key", "Handler_Key", "Channel_Key", "Supplier_Key", "Status_Key", "Severity_Key", "Risk_Key",
    }
    for table_name, csv_path, keys, data_category, sort_columns in tables:
        hidden = {column for column in pd.read_csv(csv_path, nrows=0).columns if column.endswith("_Key")}
        if table_name == "FactClaims":
            hidden |= hidden_fact
        write(
            MODEL_DEF / "tables" / f"{table_name}.tmdl",
            table_tmdl(table_name, csv_path, keys, hidden, data_category, sort_columns),
        )

    measure_lines = ["table Measures", "\tcolumn Value", "\t\tdataType: int64", "\t\tisHidden", "\t\tsummarizeBy: none", "\t\tsourceColumn: Value", ""]
    for item in measures:
        measure_lines.append(f"\t/// {item['description']}")
        measure_lines.append(f"\tmeasure {quote_tmdl(item['name'])} = {dax_literal(item['expression'])}")
        measure_lines.append(f"\t\tformatString: {item['format']}")
        measure_lines.append(f"\t\tdisplayFolder: {item['category']}")
        measure_lines.append("")
    measure_lines.extend(
        [
            "\tpartition Measures = m",
            "\t\tmode: import",
            "\t\tsource = #table(type table [Value = Int64.Type], {{1}})",
            "",
            "\tannotation PBI_ResultType = Table",
        ]
    )
    write(MODEL_DEF / "tables" / "Measures.tmdl", "\n".join(measure_lines) + "\n")

    write(MODEL_DEF / "tables" / "Investigation Capacity.tmdl", """
        table 'Investigation Capacity'
            column 'Investigation Capacity'
                dataType: int64
                isKey
                formatString: 0\"%\"
                summarizeBy: none
                sourceColumn: [Value]

            partition 'Investigation Capacity' = calculated
                mode: import
                source = GENERATESERIES ( 5, 20, 5 )

            annotation PBI_ResultType = Table
    """)
    write(MODEL_DEF / "tables" / "Analysis Metric.tmdl", """
        table 'Analysis Metric'
            column 'Analysis Metric'
                dataType: string
                sortByColumn: 'Analysis Metric Order'
                summarizeBy: none
                relatedColumnDetails:
                    groupByColumns:
                    - groupingColumn: 'Analysis Metric Fields'
                sourceColumn: [Value1]

            column 'Analysis Metric Fields'
                dataType: string
                isHidden
                sourceColumn: [Value2]
                extendedProperty ParameterMetadata = {\"version\":3,\"kind\":2}

            column 'Analysis Metric Order'
                dataType: int64
                isHidden
                summarizeBy: none
                sourceColumn: [Value3]

            partition 'Analysis Metric' = calculated
                mode: import
                source = {
                    (\"Total Incurred\", NAMEOF('Measures'[Total Incurred]), 0),
                    (\"Average Severity\", NAMEOF('Measures'[Average Severity]), 1),
                    (\"Settlement Days\", NAMEOF('Measures'[Average Settlement Days]), 2),
                    (\"SLA Compliance\", NAMEOF('Measures'[SLA Compliance %]), 3),
                    (\"Fraud Referral Rate\", NAMEOF('Measures'[Fraud Referral Rate %]), 4)
                }

            annotation PBI_ResultType = Table
            annotation PBI_Id = 7de4f9eb7d7a4cfb845c7e4c883401bc
    """)

    model_tables = [name for name, *_ in tables] + ["Measures", "Investigation Capacity", "Analysis Metric"]
    model_lines = [
        "model Model",
        "\tculture: en-ZA",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: en-ZA",
        "",
        "\tdataAccessOptions",
        "\t\tfastCombine",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
    ]
    model_lines.extend([f"ref table {quote_tmdl(name)}" for name in model_tables])
    write(MODEL_DEF / "model.tmdl", "\n".join(model_lines) + "\n")
    write(MODEL_DEF / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")

    relation_specs = [
        ("FactClaims.Loss_Date", "DimDate.Date", True),
        ("FactClaims.Report_Date", "DimDate.Date", False),
        ("FactClaims.Settlement_Date", "DimDate.Date", False),
        ("FactClaims.Product_Key", "DimProduct.Product_Key", True),
        ("FactClaims.Region_Key", "DimRegion.Region_Key", True),
        ("FactClaims.Claim_Type_Key", "DimClaimType.Claim_Type_Key", True),
        ("FactClaims.Handler_Key", "DimHandler.Handler_Key", True),
        ("FactClaims.Channel_Key", "DimChannel.Channel_Key", True),
        ("FactClaims.Supplier_Key", "DimSupplier.Supplier_Key", True),
        ("FactClaims.Status_Key", "DimStatus.Status_Key", True),
        ("FactClaims.Severity_Key", "DimSeverity.Severity_Key", True),
        ("FactClaims.Risk_Key", "DimRisk.Risk_Key", True),
        ("DataQualityIssues.Claim_ID", "FactClaims.Claim_ID", True),
    ]
    relationship_lines = []
    for index, (source, target, active) in enumerate(relation_specs, start=1):
        relationship_lines.extend(
            [
                f"relationship {stable_guid(f'relationship-{index}')}",
                f"\tfromColumn: {source}",
                f"\ttoColumn: {target}",
            ]
        )
        if not active:
            relationship_lines.append("\tisActive: false")
        relationship_lines.append("")
    write(MODEL_DEF / "relationships.tmdl", "\n".join(relationship_lines))

    root_path = r"C:\path\to\insurance-claims-intelligence-powerbi"
    write(MODEL_DEF / "expressions.tmdl", f''' 
        expression pProjectRoot = "{root_path}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
            lineageTag: {stable_guid('pProjectRoot')}

        expression fnLoadCsv = ```
                (relativePath as text, tableType as type) as table =>
                let
                    FullPath = pProjectRoot & "\\" & relativePath,
                    Source = Csv.Document(File.Contents(FullPath), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
                    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
                    TypeRecord = Type.RecordFields(Type.TableRow(tableType)),
                    Transformations = List.Transform(Record.FieldNames(TypeRecord), (columnName) => {{columnName, Record.Field(TypeRecord, columnName)[Type]}}),
                    Typed = Table.TransformColumnTypes(PromotedHeaders, Transformations)
                in
                    Typed
            ```
            lineageTag: {stable_guid('fnLoadCsv')}

        expression stg_ClaimsRaw = ```
                let
                    Source = Csv.Document(File.Contents(pProjectRoot & "\\data\\raw\\claims_raw.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
                    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
                    TrimmedText = Table.TransformColumns(PromotedHeaders, List.Transform(Table.ColumnsOfType(PromotedHeaders, {{type text}}), each {{_, Text.Trim, type text}})),
                    DuplicateFlag = Table.AddColumn(TrimmedText, "Duplicate_Flag", each if Table.RowCount(Table.SelectRows(TrimmedText, (r) => r[Claim_ID] = [Claim_ID])) > 1 then 1 else 0, Int64.Type)
                in
                    DuplicateFlag
            ```
            lineageTag: {stable_guid('stg_ClaimsRaw')}

        expression stg_ClaimsClean = ```
                let
                    Source = fnLoadCsv("data\\clean\\FactClaims.csv", type table [Claim_ID=text, Policy_ID=text, Loss_Date=date, Report_Date=date, Claim_Amount=Currency.Type, Total_Incurred=Currency.Type]),
                    ValidAmounts = Table.SelectRows(Source, each [Claim_Amount] > 0),
                    ValidDates = Table.SelectRows(ValidAmounts, each [Report_Date] >= [Loss_Date]),
                    UniqueClaims = Table.Distinct(ValidDates, {{"Claim_ID"}})
                in
                    UniqueClaims
            ```
            lineageTag: {stable_guid('stg_ClaimsClean')}
    ''')
    write(MODEL_DEF / "roles.tmdl", """
        role Executive
            modelPermission: read

        role 'Regional Manager'
            modelPermission: read

            tablePermission DimRegion =
                    DimRegion[Region] IN { "Gauteng", "Western Cape", "KwaZulu-Natal" }
    """)
    return len(relation_specs)


def column_field(table: str, column: str) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
        "queryRef": f"{table}.{column}",
        "nativeQueryRef": column,
    }


def measure_field(name: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "Measures"}}, "Property": name}},
        "queryRef": f"Measures.{name}",
        "nativeQueryRef": name,
    }


def visual_title(title: str) -> dict:
    escaped = title.replace("'", "''")
    return {
        "title": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{escaped}'"}}},
                }
            }
        ]
    }


def visual_base(visual_id: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
        "name": visual_id,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
    }


def textbox_visual(visual_id: str, text_value: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    visual = visual_base(visual_id, x, y, width, height, z)
    visual["visual"] = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text_value}]}]}}]},
    }
    return visual


def card_visual(visual_id: str, title: str, measure_name: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    visual = visual_base(visual_id, x, y, width, height, z)
    visual["visual"] = {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [measure_field(measure_name)]}}},
        "visualContainerObjects": visual_title(title),
    }
    return visual


def slicer_visual(visual_id: str, title: str, field: tuple[str, str], x: int, y: int, width: int, height: int, z: int) -> dict:
    visual = visual_base(visual_id, x, y, width, height, z)
    visual["visual"] = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [column_field(*field)]}}},
        "visualContainerObjects": visual_title(title),
    }
    return visual


def chart_visual(
    visual_id: str,
    visual_type: str,
    title: str,
    category: tuple[str, str],
    measure_name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    secondary: tuple[str, str] | None = None,
) -> dict:
    query_state = {
        "Category": {"projections": [column_field(*category)]},
        "Y": {"projections": [measure_field(measure_name)]},
    }
    if secondary:
        query_state["Series"] = {"projections": [column_field(*secondary)]}
    visual = visual_base(visual_id, x, y, width, height, z)
    visual["visual"] = {
        "visualType": visual_type,
        "query": {"queryState": query_state},
        "visualContainerObjects": visual_title(title),
    }
    return visual


def table_visual(visual_id: str, title: str, fields: list[tuple[str, str, str]], x: int, y: int, width: int, height: int, z: int) -> dict:
    projections = []
    for kind, table, prop in fields:
        projections.append(measure_field(prop) if kind == "measure" else column_field(table, prop))
    visual = visual_base(visual_id, x, y, width, height, z)
    visual["visual"] = {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": projections}}},
        "visualContainerObjects": visual_title(title),
    }
    return visual


PAGES = [
    {
        "name": "Executive Claims Overview",
        "slug": "executive-overview",
        "audience": "Claims Executive / COO",
        "kpis": ["Total Claims", "Total Incurred", "Total Paid", "Outstanding Reserve", "Average Severity", "Average Settlement Days", "SLA Compliance %", "High Risk Claims"],
        "charts": [
            ("lineChart", "Claims volume trend", ("DimDate", "Year_Month"), "Total Claims", None),
            ("lineChart", "Total incurred trend", ("DimDate", "Year_Month"), "Total Incurred", None),
            ("lineChart", "Severity trend", ("DimDate", "Year_Month"), "Average Severity", None),
            ("clusteredBarChart", "Claims by product", ("DimProduct", "Product"), "Total Claims", None),
            ("clusteredBarChart", "Claims by region", ("DimRegion", "Region"), "Total Claims", None),
            ("donutChart", "Claim status", ("DimStatus", "Claim_Status"), "Total Claims", None),
        ],
    },
    {
        "name": "Claims Operations",
        "slug": "claims-operations",
        "audience": "Claims Operations Leadership",
        "kpis": ["Average Settlement Days", "Median Settlement Days", "90th Percentile Settlement Days", "SLA Compliance %", "30+ Day Open Claims", "Awaiting Documents Claims", "Awaiting Supplier Claims", "60+ Day Open Claims"],
        "charts": [
            ("clusteredColumnChart", "Ageing distribution", ("DimStatus", "Stage_Group"), "Average Open Age", None),
            ("lineChart", "Backlog trend", ("DimDate", "Year_Month"), "30+ Day Open Claims", None),
            ("clusteredBarChart", "Claims by lifecycle stage", ("DimStatus", "Stage_Group"), "Total Claims", None),
            ("clusteredColumnChart", "Settlement time by complexity", ("FactClaims", "Claim_Complexity"), "Average Settlement Days", None),
            ("lineChart", "SLA trend", ("DimDate", "Year_Month"), "SLA Compliance %", None),
            ("clusteredBarChart", "Open claims by reason", ("DimStatus", "Claim_Status"), "Open Claims", None),
        ],
    },
    {
        "name": "Risk & Review Intelligence",
        "slug": "fraud-risk",
        "audience": "Risk / SIU Manager",
        "kpis": ["High Risk Claims", "Fraud Referral Rate %", "Investigation Capacity %", "Claims Selected for Review", "Synthetic Targets Captured", "Review Precision", "Synthetic Target Recall", "Lift vs Random Review"],
        "charts": [
            ("clusteredColumnChart", "Risk-band distribution", ("DimRisk", "Risk_Band"), "Total Claims", None),
            ("clusteredBarChart", "Risk by claim type", ("DimClaimType", "Claim_Type"), "High Risk Claims %", None),
            ("clusteredBarChart", "Risk by region", ("DimRegion", "Region"), "High Risk Claims %", None),
            ("scatterChart", "Risk vs reporting delay", ("FactClaims", "Reporting_Delay_Days"), "Fraud Referral Rate %", None),
            ("clusteredColumnChart", "Risk by severity", ("DimSeverity", "Severity_Band"), "High Risk Claims %", None),
            ("clusteredColumnChart", "Non-target review exposure", ("Investigation Capacity", "Investigation Capacity"), "Non-Target Review Rate", None),
        ],
    },
    {
        "name": "Financial Performance",
        "slug": "financial-performance",
        "audience": "Finance Executive",
        "kpis": ["Total Incurred", "Total Paid", "Outstanding Reserve", "Average Severity", "Claims per Policy", "Large Loss Count", "Large Loss Exposure", "Incurred YoY %"],
        "charts": [
            ("waterfallChart", "Incurred movement by claim type", ("DimClaimType", "Claim_Type"), "Total Incurred", None),
            ("lineChart", "Cost trend", ("DimDate", "Year_Month"), "Total Incurred", None),
            ("clusteredBarChart", "Product exposure", ("DimProduct", "Product"), "Total Incurred", None),
            ("clusteredBarChart", "Regional exposure", ("DimRegion", "Region"), "Outstanding Reserve", None),
            ("clusteredColumnChart", "Severity mix", ("DimSeverity", "Severity_Band"), "Total Incurred", None),
            ("donutChart", "Reserve concentration", ("DimClaimType", "Claim_Type"), "Outstanding Reserve", None),
        ],
    },
    {
        "name": "Regional Intelligence",
        "slug": "regional-intelligence",
        "audience": "Regional Claims Leadership",
        "kpis": ["Total Claims", "Total Incurred", "Average Severity", "Average Settlement Days", "SLA Compliance %", "Fraud Referral Rate %", "High Risk Claims", "Large Loss Exposure"],
        "charts": [
            ("map", "South African province exposure", ("DimRegion", "Region"), "Total Incurred", None),
            ("clusteredBarChart", "Claims volume by province", ("DimRegion", "Region"), "Total Claims", None),
            ("clusteredBarChart", "Average severity by province", ("DimRegion", "Region"), "Average Severity", None),
            ("clusteredColumnChart", "Settlement days by province", ("DimRegion", "Region"), "Average Settlement Days", None),
            ("clusteredColumnChart", "SLA compliance by province", ("DimRegion", "Region"), "SLA Compliance %", None),
            ("clusteredBarChart", "High-risk exposure by province", ("DimRegion", "Region"), "High Risk Claims", None),
        ],
    },
    {
        "name": "Handler Performance",
        "slug": "handler-performance",
        "audience": "Claims Team Leadership",
        "kpis": ["Claims Per Handler", "Open Claims Per Handler", "Average Severity", "Average Settlement Days", "SLA Compliance %", "Reopen Rate %", "Complaint Rate %", "Balanced Effectiveness Score"],
        "charts": [
            ("clusteredBarChart", "Workload by handler", ("DimHandler", "Handler"), "Open Claims", None),
            ("clusteredBarChart", "Service by handler", ("DimHandler", "Handler"), "SLA Compliance %", None),
            ("clusteredBarChart", "Quality by handler", ("DimHandler", "Handler"), "Handler Quality Index", None),
            ("clusteredColumnChart", "Complexity-adjusted exposure", ("DimHandler", "Handler"), "Handler Complexity Index", None),
            ("scatterChart", "Workload vs service", ("DimHandler", "Handler"), "SLA Compliance %", None),
            ("clusteredBarChart", "Balanced scorecard", ("DimHandler", "Handler"), "Balanced Effectiveness Score", None),
        ],
    },
    {
        "name": "Root Cause Analysis",
        "slug": "root-cause-analysis",
        "audience": "BI and Claims Leadership",
        "kpis": ["Selected Metric Value", "Average Severity", "Average Settlement Days", "SLA Compliance %", "Total Incurred", "Fraud Referral Rate %", "Severity YoY %", "Incurred YoY %"],
        "charts": [
            ("decompositionTreeVisual", "Why did the selected metric change?", ("DimProduct", "Product"), "Selected Metric Value", ("DimClaimType", "Claim_Type")),
            ("clusteredBarChart", "Product → claim type", ("DimClaimType", "Claim_Type"), "Selected Metric Value", ("DimProduct", "Product")),
            ("clusteredBarChart", "Region contribution", ("DimRegion", "Region"), "Selected Metric Value", None),
            ("clusteredColumnChart", "Severity-band contribution", ("DimSeverity", "Severity_Band"), "Selected Metric Value", None),
            ("clusteredColumnChart", "Channel contribution", ("DimChannel", "Channel"), "Selected Metric Value", None),
            ("lineChart", "Selected metric trend", ("DimDate", "Year_Month"), "Selected Metric Value", None),
        ],
    },
    {
        "name": "Data Quality",
        "slug": "data-quality",
        "audience": "BI Manager / Data Steward",
        "kpis": ["Completeness %", "Duplicate Rate", "Invalid Row Count", "Missing Region %", "Invalid Amount Count", "Invalid Date Count", "Data Quality Score", "Detected Data Quality Issues"],
        "charts": [
            ("clusteredBarChart", "Issues by category", ("DataQualityIssues", "Issue_Type"), "Detected Data Quality Issues", None),
            ("lineChart", "Issues over ingestion batches", ("FactClaims", "Ingestion_Batch"), "Detected Data Quality Issues", None),
            ("donutChart", "Issues by severity", ("DataQualityIssues", "Severity"), "Detected Data Quality Issues", None),
            ("clusteredColumnChart", "Validation outcomes", ("DataQualityIssues", "Resolution"), "Detected Data Quality Issues", None),
            ("clusteredBarChart", "Issue concentration by claim stage", ("DimStatus", "Stage_Group"), "Detected Data Quality Issues", None),
            ("clusteredColumnChart", "Issue counts by region", ("DimRegion", "Region"), "Detected Data Quality Issues", None),
        ],
    },
]


def create_report() -> tuple[int, int]:
    page_ids = []
    total_visuals = 0
    for page_index, page in enumerate(PAGES, start=1):
        page_id = stable_guid(f"page-{page['slug']}").replace("-", "")[:20]
        page_ids.append(page_id)
        page_dir = REPORT_DEF / "pages" / page_id
        visuals_dir = page_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        write_json(
            page_dir / "page.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
                "name": page_id,
                "displayName": page["name"],
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        visuals: list[dict] = []
        z = 1
        visuals.append(textbox_visual(stable_guid(f"{page_id}-title").replace("-", "")[:20], f"INSURANCE CLAIMS INTELLIGENCE  |  {page['name']}  |  {page['audience']}", 20, 12, 1240, 38, z)); z += 1
        visuals.append(textbox_visual(stable_guid(f"{page_id}-nav").replace("-", "")[:20], "OVERVIEW   OPERATIONS   RISK   FINANCIAL   REGIONAL   HANDLERS   ROOT CAUSE   DATA QUALITY", 20, 52, 1240, 28, z)); z += 1
        slicers = [("Date", ("DimDate", "Year_Month")), ("Product", ("DimProduct", "Product")), ("Region", ("DimRegion", "Region")), ("Risk", ("DimRisk", "Risk_Band"))]
        for slicer_index, (title, field) in enumerate(slicers):
            visuals.append(slicer_visual(stable_guid(f"{page_id}-s{slicer_index}").replace("-", "")[:20], title, field, 20 + slicer_index * 180, 84, 165, 38, z)); z += 1
        card_width = 145
        for card_index, metric_name in enumerate(page["kpis"]):
            visuals.append(card_visual(stable_guid(f"{page_id}-kpi-{card_index}").replace("-", "")[:20], metric_name, metric_name, 20 + card_index * 155, 130, card_width, 104, z)); z += 1
        for chart_index, (visual_type, title, category, metric_name, secondary) in enumerate(page["charts"]):
            row = chart_index // 3
            col = chart_index % 3
            visuals.append(chart_visual(stable_guid(f"{page_id}-chart-{chart_index}").replace("-", "")[:20], visual_type, title, category, metric_name, 20 + col * 415, 250 + row * 208, 395, 190, z, secondary)); z += 1
        disclosure = "Portfolio demonstration using synthetic data. No customer, policyholder, claim, or employer-confidential information is used."
        if page["slug"] == "fraud-risk":
            disclosure += " Risk scores prioritize review. They do not automatically determine fraud."
        if page["slug"] == "handler-performance":
            disclosure += " Workload-management demonstration—not an employee performance-management system."
        visuals.append(textbox_visual(stable_guid(f"{page_id}-disclosure").replace("-", "")[:20], disclosure, 20, 674, 1240, 28, z))
        for visual in visuals:
            write_json(visuals_dir / visual["name"] / "visual.json", visual)
        total_visuals += len(visuals)
    write_json(
        REPORT_DEF / "pages" / "pages.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": page_ids,
            "activePageName": page_ids[0],
        },
    )
    return len(page_ids), total_visuals


def svg_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def create_diagrams() -> None:
    stages = ["SYNTHETIC DATA\nGENERATOR", "RAW DATA", "DATA VALIDATION", "POWER QUERY / ETL", "STAR SCHEMA", "SEMANTIC MODEL", "DAX MEASURE LAYER", "POWER BI REPORT", "EXECUTIVE DECISION\nSUPPORT"]
    boxes = []
    arrows = []
    for index, stage in enumerate(stages):
        x = 28 + index * 142
        boxes.append(f'<rect x="{x}" y="95" width="124" height="82" rx="10" fill="{COLORS["slate"]}" stroke="{COLORS["teal"] if index in [0, 8] else "#254763"}" stroke-width="2"/>')
        line_values = stage.split("\n")
        for line_index, value in enumerate(line_values):
            boxes.append(f'<text x="{x + 62}" y="{130 + line_index * 16}" text-anchor="middle" fill="{COLORS["light"]}" font-size="11" font-weight="600">{svg_escape(value)}</text>')
        if index < len(stages) - 1:
            arrows.append(f'<path d="M {x + 124} 136 L {x + 140} 136" stroke="{COLORS["blue"]}" stroke-width="3" marker-end="url(#arrow)"/>')
    architecture = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1320" height="250" viewBox="0 0 1320 250">
      <rect width="1320" height="250" fill="{COLORS['deep_navy']}"/>
      <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="{COLORS['blue']}"/></marker></defs>
      <text x="28" y="42" fill="{COLORS['light']}" font-family="Segoe UI,Arial" font-size="24" font-weight="700">INSURANCE CLAIMS INTELLIGENCE — SOLUTION ARCHITECTURE</text>
      <text x="28" y="68" fill="{COLORS['muted']}" font-family="Segoe UI,Arial" font-size="13">Reproducible synthetic portfolio • governed transformation • decision support with human review</text>
      <g font-family="Segoe UI,Arial">{''.join(boxes)}{''.join(arrows)}</g>
      <text x="28" y="220" fill="{COLORS['amber']}" font-family="Segoe UI,Arial" font-size="12">SYNTHETIC DATA ONLY — no production or employer-confidential information</text>
    </svg>'''
    write(ASSETS / "architecture.svg", architecture)

    dims = ["DimDate", "DimProduct", "DimRegion", "DimClaimType", "DimHandler", "DimChannel", "DimSupplier", "DimStatus", "DimSeverity", "DimRisk"]
    positions = [(40, 90), (40, 210), (40, 330), (40, 450), (420, 540), (890, 450), (890, 330), (890, 210), (890, 90), (420, 60)]
    dim_elements = []
    link_elements = []
    center_x, center_y = 545, 280
    for dim, (x, y) in zip(dims, positions):
        dim_elements.append(f'<rect x="{x}" y="{y}" width="190" height="70" rx="9" fill="{COLORS["slate"]}" stroke="#254763" stroke-width="2"/><text x="{x+95}" y="{y+30}" text-anchor="middle" fill="{COLORS["light"]}" font-size="15" font-weight="700">{dim}</text><text x="{x+95}" y="{y+50}" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10">1 • single direction</text>')
        link_elements.append(f'<line x1="{x+95}" y1="{y+35}" x2="{center_x+140}" y2="{center_y+100}" stroke="{COLORS["blue"]}" stroke-width="2" opacity="0.75"/>')
    data_model = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="660" viewBox="0 0 1120 660">
      <rect width="1120" height="660" fill="{COLORS['deep_navy']}"/>
      <text x="30" y="38" fill="{COLORS['light']}" font-family="Segoe UI,Arial" font-size="24" font-weight="700">STAR SCHEMA — INSURANCE CLAIMS INTELLIGENCE</text>
      <g font-family="Segoe UI,Arial">{''.join(link_elements)}{''.join(dim_elements)}
        <rect x="545" y="280" width="280" height="200" rx="12" fill="{COLORS['navy']}" stroke="{COLORS['teal']}" stroke-width="3"/>
        <text x="685" y="320" text-anchor="middle" fill="{COLORS['light']}" font-size="21" font-weight="700">FactClaims</text>
        <text x="570" y="350" fill="{COLORS['muted']}" font-size="12">75,000 synthetic claims</text>
        <text x="570" y="375" fill="{COLORS['light']}" font-size="11">Claim_ID • Policy_ID • dates</text>
        <text x="570" y="396" fill="{COLORS['light']}" font-size="11">amounts • paid • reserve • incurred</text>
        <text x="570" y="417" fill="{COLORS['light']}" font-size="11">SLA • cycle • backlog • risk</text>
        <text x="570" y="448" fill="{COLORS['teal']}" font-size="11">∞ many-side of conformed dimensions</text>
      </g>
      <text x="30" y="630" fill="{COLORS['amber']}" font-family="Segoe UI,Arial" font-size="12">13 relationships total: 10 primary star-schema paths, 2 inactive role-playing dates, 1 audit-detail relationship.</text>
    </svg>'''
    write(ASSETS / "data-model.svg", data_model)


def load_font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf")
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError:
        return ImageFont.load_default()


def fmt_metric(metric_name: str, value: float | int) -> str:
    if any(token in metric_name for token in ["%", "Rate", "Compliance", "Recall", "Precision", "Backlog", "Completeness", "Score"]):
        if isinstance(value, (float, int)) and abs(value) <= 2:
            return f"{value:.1%}"
    if any(token in metric_name for token in ["Incurred", "Paid", "Reserve", "Severity", "Exposure", "Amount"]):
        return f"R{value / 1_000_000_000:.2f}bn" if value >= 1_000_000_000 else f"R{value / 1_000_000:.1f}m"
    return f"{value:,.1f}" if isinstance(value, float) and value % 1 else f"{value:,.0f}"


def create_mockups(metrics: dict) -> None:
    metric_values = {
        "Total Claims": metrics["claims"], "Open Claims": metrics["open_claims"], "Total Incurred": metrics["total_incurred"],
        "Total Paid": metrics["total_paid"], "Outstanding Reserve": metrics["outstanding_reserve"], "Average Severity": metrics["average_severity"],
        "Average Settlement Days": metrics["average_settlement_days"], "Median Settlement Days": metrics["median_settlement_days"],
        "90th Percentile Settlement Days": metrics["p90_settlement_days"], "SLA Compliance %": metrics["sla_compliance"],
        "High Risk Claims": metrics["high_risk_claims"], "Fraud Referral Rate %": metrics["fraud_referral_rate"],
        "Reopen Rate %": metrics["reopen_rate"], "Complaint Rate %": metrics["complaint_rate"],
        "Investigation Capacity %": 0.10, "Claims Selected for Review": metrics["capacity_scenarios"][1]["Claims_Selected"],
        "Synthetic Targets Captured": metrics["capacity_scenarios"][1]["Synthetic_Targets_Captured"], "Review Precision": metrics["capacity_scenarios"][1]["Review_Precision"],
        "Synthetic Target Recall": metrics["capacity_scenarios"][1]["Synthetic_Target_Recall"], "Lift vs Random Review": metrics["capacity_scenarios"][1]["Lift_vs_Random"],
        "Large Loss Count": 14_000, "Large Loss Exposure": metrics["total_incurred"] * 0.52, "Incurred YoY %": 0.12,
        "Claims per Policy": 1.55, "Claims Per Handler": metrics["claims"] / 30, "Open Claims Per Handler": metrics["open_claims"] / 30,
        "Balanced Effectiveness Score": 1.0, "Selected Metric Value": metrics["total_incurred"], "Severity YoY %": 0.09,
        "Completeness %": 1 - (200 + 180 + 180) / (metrics["raw_rows"] * 3), "Duplicate Rate": 150 / metrics["raw_rows"],
        "Invalid Row Count": 2000, "Missing Region %": 200 / metrics["raw_rows"], "Invalid Amount Count": 400,
        "Invalid Date Count": 350, "Data Quality Score": metrics["data_quality_score"], "Detected Data Quality Issues": metrics["detected_issues"],
        "30+ Day Open Claims": int(metrics["open_claims"] * 0.61), "60+ Day Open Claims": int(metrics["open_claims"] * 0.42),
        "Awaiting Documents Claims": int(metrics["open_claims"] * 0.25), "Awaiting Supplier Claims": int(metrics["open_claims"] * 0.17),
    }
    metric_labels = {
        "90th Percentile Settlement Days": "P90 Settlement Days",
        "Claims Selected for Review": "Claims Selected",
        "Synthetic Targets Captured": "Synthetic Targets Captured",
        "Awaiting Documents Claims": "Awaiting Documents",
        "Awaiting Supplier Claims": "Awaiting Supplier",
        "Detected Data Quality Issues": "Detected DQ Issues",
        "Balanced Effectiveness Score": "Balanced Effectiveness",
    }
    title_font, sub_font, kpi_font, kpi_value_font, small_font = load_font(28, True), load_font(13), load_font(12, True), load_font(22, True), load_font(11)
    for page_index, page in enumerate(PAGES):
        image = Image.new("RGB", (1600, 900), COLORS["deep_navy"])
        draw = ImageDraw.Draw(image)
        draw.text((40, 28), "INSURANCE CLAIMS INTELLIGENCE", font=title_font, fill=COLORS["light"])
        draw.text((40, 67), page["name"], font=sub_font, fill=COLORS["muted"])
        label = "DESIGN MOCKUP — NOT A POWER BI SCREENSHOT"
        label_box = draw.textbbox((0, 0), label, font=kpi_font)
        draw.rounded_rectangle((1110, 28, 1560, 70), radius=8, fill="#3A2D1E", outline=COLORS["amber"], width=2)
        draw.text((1335 - (label_box[2] - label_box[0]) / 2, 43), label, font=kpi_font, fill=COLORS["amber"])
        draw.rounded_rectangle((40, 98, 1560, 136), radius=7, fill=COLORS["navy"], outline="#254763")
        draw.text((60, 110), "OVERVIEW     OPERATIONS     RISK     FINANCIAL     REGIONAL     HANDLERS     ROOT CAUSE     DATA QUALITY", font=small_font, fill=COLORS["teal"])
        for index, name in enumerate(page["kpis"]):
            x = 40 + index * 190
            draw.rounded_rectangle((x, 154, x + 176, 252), radius=9, fill=COLORS["slate"], outline="#254763", width=2)
            value = metric_values.get(name, metrics["claims"] / (index + 2))
            draw.text((x + 12, 170), metric_labels.get(name, name), font=small_font, fill=COLORS["muted"])
            draw.text((x + 12, 205), fmt_metric(name, value), font=kpi_value_font, fill=COLORS["light"])
            draw.rectangle((x + 12, 238, x + 164, 241), fill=COLORS["teal"] if index % 3 != 2 else COLORS["amber"])
        chart_titles = [chart[1] for chart in page["charts"]]
        for index, chart_title in enumerate(chart_titles):
            row, col = divmod(index, 3)
            x, y = 40 + col * 507, 278 + row * 270
            draw.rounded_rectangle((x, y, x + 487, y + 244), radius=9, fill=COLORS["navy"], outline="#254763", width=2)
            draw.text((x + 18, y + 16), chart_title, font=kpi_font, fill=COLORS["light"])
            plot_left, plot_top, plot_right, plot_bottom = x + 35, y + 60, x + 457, y + 212
            draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="#35516A", width=1)
            draw.line((plot_left, plot_top, plot_left, plot_bottom), fill="#35516A", width=1)
            if index % 3 == 0:
                points = []
                for j in range(12):
                    px = plot_left + j * (plot_right - plot_left) / 11
                    py = plot_bottom - (42 + ((j * 17 + page_index * 11) % 95))
                    points.append((px, py))
                draw.line(points, fill=COLORS["teal"], width=4)
                for point in points:
                    draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3), fill=COLORS["teal"])
            else:
                for j in range(7):
                    bar_width = 38
                    bx = plot_left + 24 + j * 54
                    bar_height = 45 + ((j * 31 + page_index * 19 + index * 7) % 95)
                    draw.rounded_rectangle((bx, plot_bottom - bar_height, bx + bar_width, plot_bottom), radius=4, fill=COLORS["blue"] if j % 2 else COLORS["teal"])
            draw.text((x + 18, y + 220), "Synthetic portfolio demonstration", font=small_font, fill=COLORS["muted"])
        draw.text((40, 846), "Portfolio demonstration using synthetic data. No customer, policyholder, claim, or employer-confidential information is used.", font=small_font, fill=COLORS["muted"])
        image.save(ASSETS / f"{page['slug']}.png", format="PNG", optimize=True)
    write_json(
        ASSETS / "asset-manifest.json",
        {
            "preview_type": "DESIGN MOCKUP",
            "power_bi_screenshots": False,
            "reason": "Power BI Desktop was not available in the build environment.",
            "files": [f"{page['slug']}.png" for page in PAGES],
            "source_pages": [page["name"] for page in PAGES],
        },
    )


def create_powerquery_files() -> None:
    write(POWERQUERY / "fnLoadCsv.m", """
        // Reusable governed CSV loader used by model partitions.
        (relativePath as text, tableType as type) as table =>
        let
            FullPath = pProjectRoot & "\\" & relativePath,
            Source = Csv.Document(File.Contents(FullPath), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
            PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
            TypeRecord = Type.RecordFields(Type.TableRow(tableType)),
            Transformations = List.Transform(Record.FieldNames(TypeRecord), (columnName) => {columnName, Record.Field(TypeRecord, columnName)[Type]}),
            Typed = Table.TransformColumnTypes(PromotedHeaders, Transformations)
        in
            Typed
    """)
    write(POWERQUERY / "fnNormalizeText.m", """
        // Null-safe text normalization helper for controlled categories.
        (value as nullable any) as nullable text =>
        let
            AsText = if value = null then null else Text.From(value),
            Trimmed = if AsText = null then null else Text.Trim(AsText),
            Cleaned = if Trimmed = "" then null else Text.Clean(Trimmed)
        in
            Cleaned
    """)
    write(POWERQUERY / "stg_ClaimsRaw.m", """
        let
            Source = Csv.Document(File.Contents(pProjectRoot & "\\data\\raw\\claims_raw.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
            PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
            NormalizedText = Table.TransformColumns(PromotedHeaders, {
                {"Region", fnNormalizeText, type nullable text},
                {"Channel", fnNormalizeText, type nullable text},
                {"Claim_Type", fnNormalizeText, type nullable text},
                {"Claim_Status", fnNormalizeText, type nullable text}
            }),
            DuplicateCounts = Table.Group(NormalizedText, {"Claim_ID"}, {{"Row_Count", each Table.RowCount(_), Int64.Type}}),
            WithDuplicateFlag = Table.NestedJoin(NormalizedText, {"Claim_ID"}, DuplicateCounts, {"Claim_ID"}, "Audit", JoinKind.LeftOuter),
            ExpandedAudit = Table.ExpandTableColumn(WithDuplicateFlag, "Audit", {"Row_Count"}, {"Duplicate_Row_Count"})
        in
            ExpandedAudit
    """)
    write(POWERQUERY / "stg_ClaimsClean.m", """
        let
            Source = fnLoadCsv("data\\clean\\FactClaims.csv", type table [
                Claim_ID=text, Policy_ID=text, Loss_Date=date, Report_Date=date,
                Claim_Amount=Currency.Type, Paid_Amount=Currency.Type,
                Reserve_Amount=Currency.Type, Total_Incurred=Currency.Type
            ]),
            PositiveAmounts = Table.SelectRows(Source, each [Claim_Amount] > 0 and [Total_Incurred] >= 0),
            ValidDateOrder = Table.SelectRows(PositiveAmounts, each [Report_Date] >= [Loss_Date]),
            UniqueClaims = Table.Distinct(ValidDateOrder, {"Claim_ID"}),
            WithReportingDelay = Table.AddColumn(UniqueClaims, "Reporting_Delay_Check", each Duration.Days([Report_Date] - [Loss_Date]), Int64.Type)
        in
            WithReportingDelay
    """)
    write(POWERQUERY / "validation_rules.m", """
        let
            Source = stg_ClaimsRaw,
            WithAmountRule = Table.AddColumn(Source, "Amount_Rule", each if [Claim_Amount] = null or Number.From([Claim_Amount]) <= 0 then "FAIL" else "PASS", type text),
            WithDateRule = Table.AddColumn(WithAmountRule, "Date_Rule", each if Date.From([Report_Date]) < Date.From([Loss_Date]) then "FAIL" else "PASS", type text),
            WithCategoryRule = Table.AddColumn(WithDateRule, "Region_Rule", each if List.Contains({"Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape","Free State","Limpopo","Mpumalanga","North West","Northern Cape"}, [Region]) then "PASS" else "FAIL", type text),
            WithOutcome = Table.AddColumn(WithCategoryRule, "Validation_Outcome", each if List.Contains({[Amount_Rule], [Date_Rule], [Region_Rule]}, "FAIL") then "QUARANTINE" else "ACCEPT", type text)
        in
            WithOutcome
    """)


def create_sql_files() -> None:
    write(SQL / "01_create_dimensions.sql", """
        -- ANSI-oriented DDL; adjust identity/boolean syntax for the target platform.
        CREATE TABLE dim_date (
            date_key INTEGER PRIMARY KEY,
            calendar_date DATE NOT NULL UNIQUE,
            calendar_year INTEGER NOT NULL,
            calendar_quarter VARCHAR(2) NOT NULL,
            month_number INTEGER NOT NULL,
            month_name VARCHAR(12) NOT NULL,
            year_month VARCHAR(7) NOT NULL
        );

        CREATE TABLE dim_product (
            product_key INTEGER PRIMARY KEY,
            product_name VARCHAR(40) NOT NULL UNIQUE,
            product_description VARCHAR(200),
            portfolio VARCHAR(80) NOT NULL
        );

        CREATE TABLE dim_region (
            region_key INTEGER PRIMARY KEY,
            region_name VARCHAR(40) NOT NULL UNIQUE,
            operating_zone VARCHAR(30),
            latitude DECIMAL(9,6),
            longitude DECIMAL(9,6)
        );

        CREATE TABLE dim_claim_type (
            claim_type_key INTEGER PRIMARY KEY,
            claim_type_name VARCHAR(50) NOT NULL UNIQUE,
            cause_group VARCHAR(40) NOT NULL
        );

        CREATE TABLE dim_handler (
            handler_key INTEGER PRIMARY KEY,
            handler_name VARCHAR(50) NOT NULL UNIQUE,
            team_name VARCHAR(40) NOT NULL,
            experience_band VARCHAR(20),
            monthly_capacity INTEGER CHECK (monthly_capacity > 0)
        );

        CREATE TABLE dim_channel (
            channel_key INTEGER PRIMARY KEY,
            channel_name VARCHAR(30) NOT NULL UNIQUE,
            channel_group VARCHAR(30) NOT NULL
        );

        CREATE TABLE dim_supplier (
            supplier_key INTEGER PRIMARY KEY,
            supplier_name VARCHAR(60) NOT NULL UNIQUE,
            supplier_type VARCHAR(40),
            home_region_key INTEGER REFERENCES dim_region(region_key)
        );

        CREATE TABLE dim_status (
            status_key INTEGER PRIMARY KEY,
            claim_status VARCHAR(40) NOT NULL UNIQUE,
            stage_group VARCHAR(30) NOT NULL,
            status_order INTEGER NOT NULL,
            open_status_flag INTEGER NOT NULL CHECK (open_status_flag IN (0, 1))
        );

        CREATE TABLE dim_severity (
            severity_key INTEGER PRIMARY KEY,
            severity_band VARCHAR(20) NOT NULL UNIQUE,
            severity_order INTEGER NOT NULL,
            definition VARCHAR(80)
        );

        CREATE TABLE dim_risk (
            risk_key INTEGER PRIMARY KEY,
            risk_band VARCHAR(20) NOT NULL UNIQUE,
            risk_order INTEGER NOT NULL,
            definition VARCHAR(80)
        );
    """)
    write(SQL / "02_create_fact_claims.sql", """
        CREATE TABLE fact_claims (
            claim_id VARCHAR(20) PRIMARY KEY,
            policy_id VARCHAR(20) NOT NULL,
            loss_date DATE NOT NULL,
            report_date DATE NOT NULL,
            assignment_date DATE,
            assessment_date DATE,
            decision_date DATE,
            settlement_date DATE,
            product_key INTEGER NOT NULL REFERENCES dim_product(product_key),
            region_key INTEGER NOT NULL REFERENCES dim_region(region_key),
            claim_type_key INTEGER NOT NULL REFERENCES dim_claim_type(claim_type_key),
            handler_key INTEGER NOT NULL REFERENCES dim_handler(handler_key),
            channel_key INTEGER NOT NULL REFERENCES dim_channel(channel_key),
            supplier_key INTEGER NOT NULL REFERENCES dim_supplier(supplier_key),
            status_key INTEGER NOT NULL REFERENCES dim_status(status_key),
            severity_key INTEGER NOT NULL REFERENCES dim_severity(severity_key),
            risk_key INTEGER NOT NULL REFERENCES dim_risk(risk_key),
            claim_amount DECIMAL(18,2) NOT NULL CHECK (claim_amount > 0),
            approved_amount DECIMAL(18,2) NOT NULL,
            paid_amount DECIMAL(18,2) NOT NULL,
            reserve_amount DECIMAL(18,2) NOT NULL,
            total_incurred DECIMAL(18,2) NOT NULL,
            fraud_risk_score DECIMAL(5,2) NOT NULL CHECK (fraud_risk_score BETWEEN 0 AND 100),
            fraud_referral_flag INTEGER NOT NULL CHECK (fraud_referral_flag IN (0,1)),
            synthetic_fraud_target_flag INTEGER NOT NULL CHECK (synthetic_fraud_target_flag IN (0,1)),
            reopened_flag INTEGER NOT NULL CHECK (reopened_flag IN (0,1)),
            complaint_flag INTEGER NOT NULL CHECK (complaint_flag IN (0,1)),
            sla_target_days INTEGER NOT NULL,
            settlement_days INTEGER,
            sla_met_flag INTEGER NOT NULL CHECK (sla_met_flag IN (0,1)),
            reporting_delay_days INTEGER NOT NULL,
            prior_claims_count INTEGER NOT NULL,
            policy_tenure_months INTEGER NOT NULL,
            claim_complexity VARCHAR(20) NOT NULL,
            open_claim_age_days INTEGER NOT NULL,
            ingestion_batch VARCHAR(7) NOT NULL,
            CHECK (report_date >= loss_date),
            CHECK (settlement_date IS NULL OR settlement_date >= report_date),
            CHECK (total_incurred = paid_amount + reserve_amount)
        );

        CREATE INDEX ix_fact_claims_loss_date ON fact_claims(loss_date);
        CREATE INDEX ix_fact_claims_region_status ON fact_claims(region_key, status_key);
        CREATE INDEX ix_fact_claims_risk ON fact_claims(fraud_risk_score);
    """)
    write(SQL / "03_data_quality_checks.sql", """
        WITH validation AS (
            SELECT
                claim_id,
                CASE WHEN claim_id IS NULL OR TRIM(claim_id) = '' THEN 1 ELSE 0 END AS missing_claim_id,
                CASE WHEN claim_amount IS NULL OR claim_amount <= 0 THEN 1 ELSE 0 END AS invalid_amount,
                CASE WHEN report_date < loss_date THEN 1 ELSE 0 END AS invalid_report_order,
                CASE WHEN settlement_date IS NOT NULL AND settlement_date < report_date THEN 1 ELSE 0 END AS invalid_settlement_order,
                CASE WHEN ABS(total_incurred - (paid_amount + reserve_amount)) > 0.01 THEN 1 ELSE 0 END AS incurred_mismatch,
                COUNT(*) OVER (PARTITION BY claim_id) AS duplicate_count
            FROM fact_claims
        ), unpivoted AS (
            SELECT claim_id, 'MISSING_CLAIM_ID' AS issue_type FROM validation WHERE missing_claim_id = 1
            UNION ALL SELECT claim_id, 'INVALID_AMOUNT' FROM validation WHERE invalid_amount = 1
            UNION ALL SELECT claim_id, 'INVALID_REPORT_ORDER' FROM validation WHERE invalid_report_order = 1
            UNION ALL SELECT claim_id, 'INVALID_SETTLEMENT_ORDER' FROM validation WHERE invalid_settlement_order = 1
            UNION ALL SELECT claim_id, 'INCURRED_MISMATCH' FROM validation WHERE incurred_mismatch = 1
            UNION ALL SELECT claim_id, 'DUPLICATE_CLAIM' FROM validation WHERE duplicate_count > 1
        )
        SELECT issue_type, COUNT(*) AS issue_count, COUNT(DISTINCT claim_id) AS affected_claims
        FROM unpivoted
        GROUP BY issue_type
        ORDER BY issue_count DESC;
    """)
    write(SQL / "04_claims_performance_views.sql", """
        CREATE VIEW vw_monthly_claims_performance AS
        WITH monthly AS (
            SELECT
                EXTRACT(YEAR FROM f.loss_date) AS loss_year,
                EXTRACT(MONTH FROM f.loss_date) AS loss_month,
                COUNT(*) AS claims,
                SUM(f.total_incurred) AS total_incurred,
                AVG(f.claim_amount) AS average_severity,
                AVG(CASE WHEN f.settlement_days IS NOT NULL THEN f.settlement_days END) AS average_settlement_days,
                AVG(CAST(f.sla_met_flag AS DECIMAL(10,4))) AS sla_compliance
            FROM fact_claims f
            GROUP BY EXTRACT(YEAR FROM f.loss_date), EXTRACT(MONTH FROM f.loss_date)
        )
        SELECT
            monthly.*,
            LAG(claims, 12) OVER (ORDER BY loss_year, loss_month) AS claims_prior_year,
            LAG(total_incurred, 12) OVER (ORDER BY loss_year, loss_month) AS incurred_prior_year,
            SUM(claims) OVER (ORDER BY loss_year, loss_month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS rolling_12m_claims,
            SUM(total_incurred) OVER (ORDER BY loss_year, loss_month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS rolling_12m_incurred
        FROM monthly;

        CREATE VIEW vw_handler_balanced_scorecard AS
        SELECT
            h.handler_key,
            h.handler_name,
            h.team_name,
            COUNT(*) AS claims_handled,
            SUM(CASE WHEN s.open_status_flag = 1 THEN 1 ELSE 0 END) AS open_workload,
            AVG(f.claim_amount) AS average_claim_value,
            AVG(f.settlement_days) AS settlement_days,
            AVG(CAST(f.sla_met_flag AS DECIMAL(10,4))) AS sla_compliance,
            AVG(CAST(f.reopened_flag AS DECIMAL(10,4))) AS reopen_rate,
            AVG(CAST(f.complaint_flag AS DECIMAL(10,4))) AS complaint_rate
        FROM fact_claims f
        JOIN dim_handler h ON h.handler_key = f.handler_key
        JOIN dim_status s ON s.status_key = f.status_key
        GROUP BY h.handler_key, h.handler_name, h.team_name;
    """)
    write(SQL / "05_fraud_risk_views.sql", """
        CREATE VIEW vw_investigation_priority AS
        WITH ranked AS (
            SELECT
                f.*,
                PERCENT_RANK() OVER (ORDER BY f.fraud_risk_score DESC, f.claim_id) AS risk_rank,
                ROW_NUMBER() OVER (ORDER BY f.fraud_risk_score DESC, f.claim_amount DESC, f.claim_id) AS queue_position,
                COUNT(*) OVER () AS portfolio_claims,
                SUM(f.synthetic_fraud_target_flag) OVER () AS total_synthetic_targets
            FROM fact_claims f
        ), capacity AS (
            SELECT 5 AS capacity_pct UNION ALL
            SELECT 10 UNION ALL SELECT 15 UNION ALL SELECT 20
        )
        SELECT
            c.capacity_pct,
            r.claim_id,
            r.fraud_risk_score,
            r.queue_position,
            r.synthetic_fraud_target_flag,
            CASE WHEN r.queue_position <= CEILING(r.portfolio_claims * c.capacity_pct / 100.0) THEN 1 ELSE 0 END AS selected_for_review
        FROM ranked r
        CROSS JOIN capacity c;

        WITH capacity_results AS (
            SELECT
                capacity_pct,
                SUM(selected_for_review) AS selected_claims,
                SUM(CASE WHEN selected_for_review = 1 THEN synthetic_fraud_target_flag ELSE 0 END) AS captured_targets,
                SUM(synthetic_fraud_target_flag) AS total_targets,
                COUNT(DISTINCT claim_id) AS total_claims
            FROM vw_investigation_priority
            GROUP BY capacity_pct
        )
        SELECT
            capacity_pct,
            selected_claims,
            captured_targets,
            captured_targets * 1.0 / NULLIF(selected_claims, 0) AS review_precision,
            captured_targets * 1.0 / NULLIF(total_targets, 0) AS synthetic_target_recall,
            1 - captured_targets * 1.0 / NULLIF(selected_claims, 0) AS non_target_review_rate,
            (captured_targets * 1.0 / NULLIF(selected_claims, 0)) /
                NULLIF(total_targets * 1.0 / total_claims, 0) AS lift_vs_random
        FROM capacity_results
        ORDER BY capacity_pct;
    """)
    write(SQL / "06_financial_analysis.sql", """
        WITH segment_financials AS (
            SELECT
                p.product_name,
                ct.claim_type_name,
                r.region_name,
                COUNT(*) AS claims,
                SUM(f.paid_amount) AS paid,
                SUM(f.reserve_amount) AS outstanding_reserve,
                SUM(f.total_incurred) AS total_incurred,
                AVG(f.claim_amount) AS average_severity,
                SUM(CASE WHEN f.claim_amount >= 250000 THEN f.total_incurred ELSE 0 END) AS large_loss_exposure
            FROM fact_claims f
            JOIN dim_product p ON p.product_key = f.product_key
            JOIN dim_claim_type ct ON ct.claim_type_key = f.claim_type_key
            JOIN dim_region r ON r.region_key = f.region_key
            GROUP BY p.product_name, ct.claim_type_name, r.region_name
        ), ranked AS (
            SELECT
                segment_financials.*,
                RANK() OVER (PARTITION BY product_name ORDER BY total_incurred DESC) AS exposure_rank,
                SUM(total_incurred) OVER (PARTITION BY product_name) AS product_incurred,
                SUM(outstanding_reserve) OVER () AS portfolio_reserve
            FROM segment_financials
        )
        SELECT
            *,
            total_incurred / NULLIF(product_incurred, 0) AS share_of_product_incurred,
            outstanding_reserve / NULLIF(portfolio_reserve, 0) AS share_of_portfolio_reserve
        FROM ranked
        WHERE exposure_rank <= 10
        ORDER BY product_name, exposure_rank;
    """)


FIELD_DESCRIPTIONS = {
    "Claim_ID": "Synthetic claim identifier and fact-table grain.",
    "Policy_ID": "Synthetic policy identifier; policies may have multiple legitimate claims.",
    "Loss_Date": "Date on which the simulated insured event occurred.",
    "Report_Date": "Date on which the simulated claim was reported.",
    "Assignment_Date": "Date on which a handler was assigned.",
    "Assessment_Date": "Date of simulated assessment completion.",
    "Decision_Date": "Date of simulated claim decision.",
    "Settlement_Date": "Date of settlement; blank for unsettled claims.",
    "Claim_Amount": "Gross amount claimed in South African Rand.",
    "Approved_Amount": "Simplified approved amount in South African Rand.",
    "Paid_Amount": "Simplified paid amount in South African Rand.",
    "Reserve_Amount": "Simplified outstanding case reserve in South African Rand.",
    "Total_Incurred": "Paid amount plus outstanding reserve; not actuarial ultimate loss.",
    "Fraud_Risk_Score": "Synthetic review-prioritization index from 0 to 100; not proof of fraud.",
    "Fraud_Referral_Flag": "Indicates a simulated referral to a human investigation queue.",
    "Synthetic_Fraud_Target_Flag": "Synthetic outcome used only to demonstrate precision, recall and lift.",
    "Risk_Rank_Percentile": "Portfolio percentile of the synthetic risk score.",
    "Review_Priority": "Operational priority band derived from risk score thresholds.",
    "Investigation_Capacity_Pct": "Illustrative share of claims that can be selected for analyst review.",
    "Claims_Selected": "Claims included in the capacity-constrained synthetic review queue.",
    "Synthetic_Targets_Captured": "Synthetic demonstration target events included in the selected queue.",
    "Review_Precision": "Synthetic target events divided by claims selected for review.",
    "Synthetic_Target_Recall": "Share of all synthetic demonstration target events included in the selected queue.",
    "Non_Target_Review_Rate": "Share of selected claims without the synthetic target flag; not a real false-positive rate.",
    "Lift_vs_Random": "Review precision divided by the portfolio-wide synthetic target rate.",
    "Reopened_Flag": "Indicates that a claim was synthetically reopened.",
    "Complaint_Flag": "Indicates a simulated complaint linked to the claim.",
    "Documentation_Missing_Flag": "Latent synthetic feature representing missing documentation during handling.",
    "SLA_Target_Days": "Complexity-based simulated target cycle time.",
    "Settlement_Days": "Days from report to settlement; blank for unsettled claims.",
    "SLA_Met_Flag": "One when the observed or open age is within the target, otherwise zero.",
    "Reporting_Delay_Days": "Days from loss to report.",
    "Prior_Claims_Count": "Synthetic count of earlier claims for the policy.",
    "Policy_Tenure_Months": "Synthetic policy tenure at claim time.",
    "Claim_Complexity": "Standard, Moderate, Complex or Specialist operational band.",
    "Open_Claim_Age_Days": "Age at 2026-08-31 for non-terminal claims; zero for terminal claims.",
    "Assignment_Days": "Days from report to assignment.",
    "Assessment_Days": "Days from assignment to assessment.",
    "Decision_Days": "Days from assessment to decision.",
    "Lifecycle_Stage": "Operational stage aligned to the current claim status.",
    "Ingestion_Batch": "Synthetic monthly ingestion batch in YYYY-MM format.",
    "Issue_ID": "Unique detected data-quality issue event.",
    "Issue_Type": "Governed category of the detected defect.",
    "Severity": "Operational severity assigned to the quality issue.",
    "Original_Value": "Defective raw value as detected.",
    "Corrected_Value": "Value used by the deterministic correction pipeline.",
    "Resolution": "Plain-language remediation applied by the clean build.",
}


DERIVED_FIELDS = {
    "Approved_Amount", "Paid_Amount", "Reserve_Amount", "Total_Incurred", "Fraud_Risk_Score",
    "Fraud_Referral_Flag", "Synthetic_Fraud_Target_Flag", "Risk_Rank_Percentile", "Review_Priority",
    "Reopened_Flag", "Complaint_Flag", "SLA_Target_Days", "Settlement_Days", "SLA_Met_Flag",
    "Reporting_Delay_Days", "Claim_Complexity", "Open_Claim_Age_Days", "Assignment_Days",
    "Assessment_Days", "Decision_Days", "Lifecycle_Stage", "Ingestion_Batch", "Date_Key",
    "Year", "Quarter", "Month_Number", "Month", "Month_Short", "Year_Month", "Year_Month_Sort",
    "Week", "Day", "Day_Name", "Is_Month_End", "Severity_Band", "Risk_Band",
}


def source_logic(column: str) -> str:
    if column.endswith("_Key"):
        return "Deterministic surrogate-key mapping to the conformed dimension."
    if column in {"Claim_ID", "Policy_ID"}:
        return "Deterministic synthetic identifier generated from the fixed seed."
    if column in {"Total_Incurred"}:
        return "Paid_Amount + Reserve_Amount."
    if column in {"Reporting_Delay_Days", "Assignment_Days", "Assessment_Days", "Decision_Days", "Settlement_Days", "Open_Claim_Age_Days"}:
        return "Calculated from validated lifecycle dates."
    if column in {"Severity_Band", "Risk_Band", "Review_Priority", "Claim_Complexity"}:
        return "Rule-based banding of synthetic amount, risk or complexity features."
    if column.endswith("_Flag"):
        return "Deterministic business rule or seeded synthetic outcome."
    if column.startswith("Issue") or column in {"Original_Value", "Corrected_Value", "Resolution"}:
        return "Generated by the raw-data validation and remediation audit pipeline."
    return "Generated from documented synthetic portfolio logic or dimension metadata."


def markdown_safe(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def create_data_dictionary() -> tuple[str, int]:
    table_files = sorted(CLEAN.glob("*.csv")) + [DATA / "data_quality_issues.csv"]
    rows = []
    for csv_file in table_files:
        table_name = csv_file.stem
        frame = pd.read_csv(csv_file, low_memory=False)
        for column in frame.columns:
            series = frame[column]
            non_null = series.dropna()
            example = "" if non_null.empty else non_null.iloc[0]
            if isinstance(example, float):
                example = f"{example:.4f}"
            dtype = infer_tmdl_type(column, series.dtype)
            rows.append(
                {
                    "Field Name": column,
                    "Table": table_name,
                    "Data Type": dtype,
                    "Business Definition": FIELD_DESCRIPTIONS.get(column, column.replace("_", " ").capitalize() + "."),
                    "Example": example,
                    "Nullable?": "Yes" if series.isna().any() else "No",
                    "Derived?": "Yes" if column in DERIVED_FIELDS or column.endswith("_Key") else "No",
                    "Source Logic": source_logic(column),
                }
            )
    header = "| Field Name | Table | Data Type | Business Definition | Example | Nullable? | Derived? | Source Logic |\n|---|---|---|---|---|---|---|---|\n"
    body = "\n".join("| " + " | ".join(markdown_safe(row[key]) for key in row) + " |" for row in rows)
    return header + body + "\n", len(rows)


def create_dax_docs(measures: list[dict]) -> None:
    sections = [
        "# DAX measure layer",
        "",
        f"The dedicated `Measures` table contains **{len(measures)} explicit measures**. Implicit measures are discouraged in `model.tmdl`. Currency measures use South African Rand formatting, ratios use `DIVIDE`, and time intelligence uses the conformed `DimDate` table.",
        "",
        "> Risk and target measures operate on synthetic demonstration labels. A risk score prioritizes human review; it does not determine fraud.",
        "",
    ]
    for category in sorted({item["category"] for item in measures}):
        sections.extend([f"## {category}", ""])
        for item in [m for m in measures if m["category"] == category]:
            sections.extend(
                [
                    f"### {item['name']}",
                    "",
                    item["description"],
                    "",
                    "```DAX",
                    f"{item['name']} = {item['expression']}",
                    "```",
                    "",
                    f"Format: `{item['format']}`",
                    "",
                ]
            )
    write(DAX / "measures.md", "\n".join(sections))
    write(DAX / "field-parameters.dax", """
        // Equivalent DAX for the TMDL field-parameter table.
        Analysis Metric = {
            ("Total Incurred", NAMEOF('Measures'[Total Incurred]), 0),
            ("Average Severity", NAMEOF('Measures'[Average Severity]), 1),
            ("Settlement Days", NAMEOF('Measures'[Average Settlement Days]), 2),
            ("SLA Compliance", NAMEOF('Measures'[SLA Compliance %]), 3),
            ("Fraud Referral Rate", NAMEOF('Measures'[Fraud Referral Rate %]), 4)
        }
    """)


def create_docs(metrics: dict, findings: list[dict], measures: list[dict], relationships: int, pages: int, visuals: int) -> int:
    dictionary, field_count = create_data_dictionary()
    write(DOCS / "data-dictionary.md", "# Data dictionary\n\nThis dictionary covers every physical field delivered in the clean star-schema and quality-audit extracts.\n\n" + dictionary)
    write(DOCS / "architecture.md", f"""
        # Architecture

        ![Solution architecture](../assets/architecture.svg)

        The solution is a local, file-backed PBIP portfolio demonstration. `generate_synthetic_claims.py` produces a reproducible raw extract. `validate_data.py` independently verifies every controlled defect and writes a row-level audit log. `build_clean_dataset.py` applies the governed corrections, enforces business rules, and materializes a star schema. Power Query expressions load those governed extracts into the TMDL semantic model; {len(measures)} explicit DAX measures support eight PBIR report pages.

        The model uses Power BI Project source files rather than a fabricated PBIX. The project follows Microsoft's current PBIP properties, PBIR definition and semantic-model definition schema URLs embedded in each JSON file.

        Microsoft references: [Power BI Projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR report project files](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [enhanced PBIR](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format), [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), and the [report 3.2.0 JSON Schema](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.2.0/schema.json).

        ## Runtime flow

        1. Fixed seed `20260831` generates 75,000 synthetic claims.
        2. A separate raw layer contains 2,150 controlled quality issue events and 150 duplicate rows.
        3. Validation checks each condition and records the correction decision.
        4. The clean build applies corrections, removes the later duplicates and verifies business invariants.
        5. Ten dimensions and `FactClaims` are loaded through reusable M.
        6. Single-direction relationships propagate dimension filters to the fact.
        7. Explicit DAX measures power executive, operational, financial, regional, risk and quality views.

        ## Deployment boundary

        The source is designed for Power BI Desktop. A production implementation would replace local CSVs with governed lakehouse, warehouse or database sources; add environment parameters and deployment pipelines; and validate security, refresh, lineage and performance in the target tenant.
    """)
    write(DOCS / "data-model.md", f"""
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

        The model contains **{relationships} relationships**. No bidirectional filter is used. `Measures`, `Investigation Capacity`, and `Analysis Metric` are disconnected semantic helper tables. The audit relationship deliberately treats the unique claim ID in `FactClaims` as the one-side so claim batch and segment filters can contextualize quality issues.

        `Total_Incurred` is a simplified paid-plus-case-reserve value. It is not an actuarial ultimate-loss estimate.
    """)
    write(DOCS / "power-query.md", """
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
    """)
    write(DOCS / "methodology.md", """
        # Methodology

        ## Synthetic portfolio generation

        The fixed NumPy seed is `20260831`. Loss dates span 2024-01-01 through 2026-08-31, with a modest volume trend and seasonal weather uplift. Product, claim type, province and channel are sampled from documented conditional distributions. Amounts use claim-type baselines, portfolio and regional factors, severity inflation, weather seasonality and a capped log-normal distribution.

        Operational fields are correlated by construction. Complexity rises with amount and selected claim types. Missing documentation adds assessment and decision delay. Two simulated backlog windows add cycle time. Large or complex claims generally settle more slowly and carry larger simplified case reserves. Complaints and reopening are more likely when SLA or complexity signals are adverse.

        The risk score combines reporting delay, prior claims, theft/fire indicators, large-loss status, channel, policy tenure and small regional effects, plus noise. `Synthetic_Fraud_Target_Flag` is a clearly named seeded demonstration outcome used to calculate review precision, synthetic-target recall and lift. Neither field represents a real fraud model or confirms fraud.

        ## Quality challenge

        Exactly 2,150 controlled issue events are seeded across a still-usable raw extract. Each event has a stable raw-row identifier, correction value and resolution. Validation proves that the observed raw condition matches the manifest before the clean build applies it. The later copy of each duplicate claim is removed.

        ## Analytical stance

        Findings are calculated only after the clean dataset exists. They describe association and concentration in a synthetic portfolio. No causal, actuarial, production or workplace-performance claim is made.
    """)
    insight_sections = ["# Synthetic executive insights", "", "All findings below are calculated from the generated dataset. They are demonstration results, not workplace achievements or production evidence.", ""]
    for index, item in enumerate(findings, start=1):
        insight_sections.extend(
            [
                f"## {index}. {item['title']}", "",
                f"**Observation:** {item['observation']}", "",
                f"**Evidence:** {item['evidence']}", "",
                f"**Business implication:** {item['business_implication']}", "",
                f"**Possible action:** {item['possible_action']}", "",
            ]
        )
    write(DOCS / "executive-insights.md", "\n".join(insight_sections))

    validation = json.loads((DATA / "validation_summary.json").read_text(encoding="utf-8"))
    issue_rows = textwrap.indent("\n".join(f"| {name} | {count:,} |" for name, count in validation["issues_by_type"].items()), "        ")
    write(DOCS / "data-quality.md", f"""
        # Data quality challenge

        The raw layer contains **{metrics['raw_rows']:,} rows** for **{metrics['claims']:,} canonical claims**. It includes **{metrics['seeded_issues']:,} controlled issue events** ({metrics['seeded_issues']/metrics['claims']:.2%} of canonical claim count). Validation detected all **{metrics['detected_issues']:,}** events; the clean fact contains 75,000 unique positive-amount claims with valid primary date ordering.

        | Issue type | Detected events |
        |---|---:|
{issue_rows}

        ## Controls

        - Preserve raw evidence and stable raw-row IDs.
        - Detect before correcting; fail the build if a seeded condition is not observed.
        - Quarantine logic is demonstrated in M; the executable build uses explicit correction records.
        - Remove only the known later duplicate rows.
        - Enforce positive amounts, valid date order, governed categories and unique claim grain.
        - Reconcile paid plus reserve to total incurred.

        `Data Quality Score` is a transparent portfolio-demo index: `1 - detected issue events / raw rows` = **{metrics['data_quality_score']:.1%}**. It is not an industry standard.
    """)
    write(DOCS / "limitations.md", """
        # Limitations

        - All data is synthetic and has no production validation.
        - The portfolio does not represent real customer behaviour, policy terms or market mix.
        - The risk score is not a real fraud model and does not confirm fraud.
        - The claims lifecycle, documentation state and supplier activity are simplified.
        - Reserves are simplified case-reserve values; there is no actuarial reserving or IBNR model.
        - Correlations were designed for demonstration and do not support causal interpretation.
        - Currency values are illustrative South African Rand amounts, not financial forecasts.
        - Handler analytics are a workload-management demonstration, not an employee performance-management system.
        - RLS is a conceptual role definition with no real users, identity mapping or tenant testing.
        - PBIR pages were authored as source files without Power BI Desktop rendering in the build environment.
        - Preview images are explicitly labelled design mockups, not screenshots of rendered Power BI output.
    """)
    write(DOCS / "row-level-security.md", """
        # Row-level security

        Two conceptual roles are defined in `roles.tmdl`:

        - **Executive** has read access to the full model.
        - **Regional Manager** is restricted to a demonstration set of Gauteng, Western Cape and KwaZulu-Natal.

        No real users, email addresses or identity provider values are included. In production, replace the static filter with a governed user-to-region bridge and `USERPRINCIPALNAME()`, validate effective identity in the service, and test export, Analyze in Excel, drill-through and subscription behaviour.

        The example demonstrates model security structure only. It must not be treated as a deployed access-control design.
    """)
    write(DOCS / "power-bi-setup.md", f"""
        # Power BI Desktop setup

        ## Open and refresh

        1. Install a current Power BI Desktop release that supports PBIP, PBIR and TMDL preview features.
        2. Clone or unzip the repository.
        3. Regenerate the data if desired using the commands in the root README.
        4. Open `InsuranceClaimsIntelligence.pbip`.
        5. If the repository moved, edit the `pProjectRoot` Power Query parameter to the new absolute repository path.
        6. Import `theme/insurance-intelligence-theme.json` if Desktop does not automatically retain an external theme reference.
        7. Confirm that `DimDate[Date]` is recognized as the model's marked date column and refresh.
        8. Inspect relationships, roles and the {len(measures)}-measure `Measures` table before publishing.

        ## Desktop-only finishing checks

        Power BI Desktop was not available in the build environment. The PBIR source contains all eight pages, bound KPI/chart definitions, slicers and disclosure text. In Desktop, verify visual role mappings for the installed report schema, then configure or confirm bookmarks, synced slicers, reset-filter actions, report-tooltip targets, provincial drill-through and phone layouts. These interaction states require a rendering host and are not claimed as runtime-tested here.

        Use the exact [Desktop verification checklist](desktop-verification-checklist.md) and record only observed results in [Power BI runtime verification](power-bi-runtime-verification.md).

        ## Save as PBIX

        After a successful refresh and interaction check, use **File → Save a copy** and select `.pbix` if a binary distribution is needed. This repository intentionally does not fabricate or commit a PBIX.
    """)
    page_rows = textwrap.indent("\n".join(f"| {i} | {page['name']} | {page['audience']} | {', '.join(chart[1] for chart in page['charts'])} |" for i, page in enumerate(PAGES, start=1)), "        ")
    write(DOCS / "report-pages.md", f"""
        # Report page specification

        The enhanced PBIR report contains **{pages} pages and {visuals} visual containers**. Standard Power BI page tabs provide navigation; each page also has a consistent navigation header, four primary slicers and a synthetic-data disclosure.

        | # | Page | Audience | Analytical views |
        |---:|---|---|---|
{page_rows}

        ## UX implementation status

        | Feature | Status |
        |---|---|
        | Enhanced PBIR page definitions | Source-configured |
        | Standard page-tab navigation and executive nav header | Source-configured |
        | Date, product, region and risk slicers | Source-configured |
        | Investigation-capacity what-if table (5/10/15/20) | TMDL-configured |
        | Analysis metric field-parameter table | TMDL-configured |
        | Dynamic executive attention measures | DAX-configured |
        | RLS roles | TMDL-configured, conceptual only |
        | Enhanced tooltips setting | Enabled in report metadata |
        | Theme, accessible high-contrast palette | Delivered as importable JSON |
        | Bookmarks, reset action, synced slicers, drill-through target, phone layouts | Desktop verification/configuration required |

        Risk scores prioritize review. They do not automatically determine fraud. Handler views are for balanced workload management, not employee performance management.

        Recruiter-facing page purposes and captions are documented in [report-page-guide.md](report-page-guide.md).
    """)
    return field_count


def create_readme(metrics: dict, findings: list[dict], measures: list[dict], relationships: int, pages: int, visuals: int, field_count: int) -> None:
    findings_md = "\n".join(f"{index}. **{item['title']}** — {item['evidence']}" for index, item in enumerate(findings[:6], start=1))
    findings_md = textwrap.indent(findings_md, "        ")
    write(ROOT / "README.md", f"""
        # Insurance Claims Intelligence

        [![Project QA](https://github.com/GarethMackenzie/insurance-claims-intelligence-powerbi/actions/workflows/ci.yml/badge.svg)](https://github.com/GarethMackenzie/insurance-claims-intelligence-powerbi/actions/workflows/ci.yml)

        ## Executive Claims Performance, Risk & Operational Analytics

        > **Portfolio demonstration using synthetic data only.** No customer, policyholder, claim, or employer-confidential information is used. All findings are synthetic portfolio findings, not workplace achievements.

        **Source/runtime status:** Structurally validated from PBIP/PBIR/TMDL source. Final visual rendering and interaction verification requires a current Power BI Desktop host.

        **Portfolio evidence:** {metrics['claims']:,} synthetic claims · {len(measures)} DAX measures · {pages} report pages · PBIP/PBIR/TMDL · Power Query · Python · SQL · automated QA and GitHub Actions

        ## Executive Summary

        This is a source-controlled Power BI decision-support project for claims performance, financial exposure, service, backlog and risk-based human review. It combines reproducible data engineering with an inspectable semantic model and executive analytical storytelling.

        ## Business Problem

        Claims leaders need a governed view of cost, severity, lifecycle delay, SLA, backlog, reserve exposure, regional concentration and limited fraud-review capacity. This solution is designed around management questions: what changed, where pressure is building, why it matters, and what to investigate next.

        ## Solution Overview

        **Problem:** Claims leaders need trustworthy visibility into cost, delays, reserves, SLA and constrained risk-review capacity.

        **Approach:** Synthetic generation → validation → governed cleaning → star schema → Power Query → TMDL → DAX → PBIR → executive report → automated QA.

        **Result:** A reproducible, privacy-safe executive analytics solution. Synthetic financial values are demonstration results, not workplace achievements.

        | Capability | Evidence in this repository |
        |---|---|
        | Governed data pipeline | Deterministic Python generation, independent validation, correction audit and clean star-schema build |
        | Power BI engineering | Editable PBIP, enhanced PBIR and TMDL source with explicit relationships and a dedicated measure table |
        | Claims analytics | Executive, operations, financial, regional, handler, root-cause, risk-review and data-quality views |
        | Analytical depth | {len(measures)} DAX measures, reusable Power Query M, six SQL modules and a capacity-constrained review simulator |
        | Quality controls | Reproducibility, reconciliation, semantic-model, privacy, asset, link and CI contract checks |

        ## Executive Portfolio Snapshot

        | Metric | Synthetic result |
        |---|---:|
        | Claims | {metrics['claims']:,} |
        | Open claims | {metrics['open_claims']:,} |
        | Total incurred | R{metrics['total_incurred']/1_000_000_000:.2f}bn |
        | Outstanding reserve | R{metrics['outstanding_reserve']/1_000_000_000:.2f}bn |
        | Average severity | R{metrics['average_severity']:,.0f} |
        | Median settlement days | {metrics['median_settlement_days']:.0f} |
        | SLA compliance | {metrics['sla_compliance']:.1%} |
        | High/Critical risk share | {metrics['high_risk_rate']:.1%} |
        | Data quality detection | {metrics['detected_issues']:,} / {metrics['seeded_issues']:,} ({metrics['detected_issues']/metrics['seeded_issues']:.0%}) |

        ### Key synthetic findings

{findings_md}

        Evidence, implications and cautious action framing are in [executive-insights.md](docs/executive-insights.md).

        ## Architecture

        ![Insurance Claims Intelligence solution architecture](assets/architecture.svg)

        `synthetic raw data → validation audit → governed clean star schema → Power Query → TMDL semantic model → enhanced PBIR report source → automated QA`

        See [architecture](docs/architecture.md) and [methodology](docs/methodology.md).

        ## Dashboard / Report Pages

        These images are **design mockups, not Power BI screenshots**. The editable visual definitions are in [`InsuranceClaimsIntelligence.Report`](InsuranceClaimsIntelligence.Report/definition/pages/).

        | Executive overview | Claims operations |
        |---|---|
        | ![Executive overview design mockup](assets/executive-overview.png) | ![Claims operations design mockup](assets/claims-operations.png) |
        | Risk & review | Financial performance |
        | ![Risk and review design mockup](assets/fraud-risk.png) | ![Financial performance design mockup](assets/financial-performance.png) |
        | Regional intelligence | Handler performance |
        | ![Regional intelligence design mockup](assets/regional-intelligence.png) | ![Handler performance design mockup](assets/handler-performance.png) |
        | Root-cause analysis | Data quality |
        | ![Root cause design mockup](assets/root-cause-analysis.png) | ![Data quality design mockup](assets/data-quality.png) |

        Page scope and implementation status are documented in [report-pages.md](docs/report-pages.md).

        Recruiter-focused captions and management decisions are in the [report page guide](docs/report-page-guide.md).

        ## Data Model

        ![Insurance claims star schema](assets/data-model.svg)

        `FactClaims` is one row per claim. Ten conformed dimensions filter it in a single direction across {relationships} relationships. `DimDate[Date]` is the marked date column; loss date is active, while report and settlement dates are inactive role-playing paths. The complete [data dictionary](docs/data-dictionary.md) documents {field_count} physical fields.

        ## DAX & Semantic Layer

        The model discourages implicit measures and provides {len(measures)} documented measures for financial exposure, severity, service, backlog, time intelligence, review capacity and balanced workload analysis. Ratios use `DIVIDE`; open-claim logic uses the governed status flag; month, status, severity and risk labels have explicit sort columns. See the [DAX catalogue](dax/measures.md).

        ## Power Query & Data Quality

        Reusable M centralizes UTF-8 CSV loading and schema enforcement. The raw layer contains {metrics['raw_rows']:,} rows and {metrics['seeded_issues']:,} controlled issue events; validation detects every event before the clean build applies explicit corrections and reconciles to {metrics['claims']:,} unique claims. See [Power Query design](docs/power-query.md) and [data-quality evidence](docs/data-quality.md).

        ## SQL Analytics

        [`sql/`](sql/) contains six ANSI-oriented modules covering dimensional DDL, validation controls, lifecycle performance, review-capacity prioritization and financial exposure. The examples use CTEs, guarded division, CASE expressions and window functions.

        ## Reproducibility

        The fixed seed `20260831`, project-relative inputs and deterministic scripts reproduce the dataset and source artifacts. Run the pipeline in this order: generate → validate → clean build → project build → QA.

        ## Quality Assurance

        `python scripts/qa_project.py` reruns the full build and tests data grain, controlled defects, financial reconciliation, date semantics, PBIP/PBIR references, TMDL structure, DAX conventions, CI wiring, SQL/Python syntax, internal links, privacy and mockup integrity. The latest evidence is in [qa-report.md](docs/qa-report.md).

        Automated QA does not prove rendering. The separate [runtime evidence record](docs/power-bi-runtime-verification.md) remains **MANUAL REVIEW**, with exact steps in the [Desktop verification checklist](docs/desktop-verification-checklist.md).

        ## Recruiter Walkthrough

        A natural [60–90 second walkthrough](docs/project-walkthrough.md) and [technical interview guide](docs/interview-guide.md) explain the business problem, architecture, semantic-model decisions, responsible analytics and production boundary without presenting synthetic results as workplace achievements.

        ## Responsible Analytics & Limitations

        Risk scores prioritize human review; they never determine fraud or automate a claim decision. Synthetic targets exist only to demonstrate queue metrics. Reserves are simplified case reserves, RLS is conceptual, and handler views support workload management rather than employee evaluation. See [limitations](docs/limitations.md) and [RLS notes](docs/row-level-security.md).

        ## How to Run

        From the repository root:

        ```powershell
        python -m venv .venv
        .venv\\Scripts\\Activate.ps1
        pip install -r requirements.txt
        python scripts/generate_synthetic_claims.py
        python scripts/validate_data.py
        python scripts/build_clean_dataset.py
        python scripts/build_project.py
        python scripts/qa_project.py
        ```

        Open [`InsuranceClaimsIntelligence.pbip`](InsuranceClaimsIntelligence.pbip) in a current Power BI Desktop release, set `pProjectRoot` to the clone path, refresh, and complete the [Desktop verification checklist](docs/desktop-verification-checklist.md). Setup details are in [power-bi-setup.md](docs/power-bi-setup.md).

        ## Repository Structure

        ```text
        InsuranceClaimsIntelligence.pbip
        InsuranceClaimsIntelligence.Report/       enhanced PBIR report source
        InsuranceClaimsIntelligence.SemanticModel/ TMDL semantic model source
        data/raw/ and data/clean/                  reproducible synthetic extracts
        scripts/                                   generation, validation, clean build and QA
        powerquery/                                reusable M and staging examples
        dax/                                       measure catalogue and field parameter
        sql/                                       six analytical SQL modules
        docs/                                      architecture, method, governance and setup
        assets/                                    diagrams and labelled design mockups
        theme/                                     Power BI theme JSON
        ```

        ## Author

        **Gareth Andrew Mackenzie**<br>
        Johannesburg, South Africa

        `Power BI` · `DAX` · `Power Query` · `TMDL` · `PBIP/PBIR` · `Python` · `SQL` · `Insurance analytics`

        Licensed under the [MIT License](LICENSE).
    """)


def main() -> None:
    required = [DATA / "portfolio_metrics.json", DATA / "executive_insights.json", CLEAN / "FactClaims.csv"]
    if not all(path.exists() for path in required):
        raise FileNotFoundError("Run the three data-pipeline scripts before build_project.py.")
    metrics = json.loads((DATA / "portfolio_metrics.json").read_text(encoding="utf-8"))
    findings = json.loads((DATA / "executive_insights.json").read_text(encoding="utf-8"))
    measures = build_measures(metrics)
    create_foundation(metrics)
    relationships = create_semantic_model(measures)
    pages, visuals = create_report()
    create_diagrams()
    create_mockups(metrics)
    create_powerquery_files()
    create_sql_files()
    create_dax_docs(measures)
    field_count = create_docs(metrics, findings, measures, relationships, pages, visuals)
    create_readme(metrics, findings, measures, relationships, pages, visuals, field_count)
    build_summary = {
        "tables": 15,
        "physical_dimensions": 10,
        "relationships": relationships,
        "dax_measures": len(measures),
        "report_pages": pages,
        "visual_containers": visuals,
        "documented_fields": field_count,
        "design_mockups": len(PAGES),
    }
    write_json(DATA / "build_summary.json", build_summary)
    print(f"Built PBIP project: {pages} pages, {visuals} visual containers, {len(measures)} measures, {relationships} relationships.")


if __name__ == "__main__":
    main()
