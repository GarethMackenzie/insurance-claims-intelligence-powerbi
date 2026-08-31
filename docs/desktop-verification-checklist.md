# Power BI Desktop verification checklist

Use this checklist in a current Power BI Desktop release after cloning the repository. It is deliberately separate from automated QA: Python can validate source structure and data invariants, but it cannot prove that Desktop rendered visuals or executed interactions.

Record verified outcomes in [`power-bi-runtime-verification.md`](power-bi-runtime-verification.md). Leave a result as **MANUAL REVIEW** until the named test has actually been performed.

## 1. Prepare a clean test environment

- [ ] Use a current 64-bit Power BI Desktop release with PBIP, enhanced PBIR and TMDL support.
- [ ] Note the exact version from **Help → About**.
- [ ] Clone the repository to a path that contains no confidential project or customer names.
- [ ] Run the complete Python pipeline from the repository root.
- [ ] Confirm `python scripts/qa_project.py` passes.
- [ ] Close unrelated applications and suppress notifications before capturing evidence.

## 2. Open and refresh

1. Open `InsuranceClaimsIntelligence.pbip`.
2. If prompted, enable the required preview features and restart Desktop.
3. Set `pProjectRoot` to the repository's absolute clone path.
4. Select **Transform data → Data source settings** and confirm that all model sources resolve beneath `pProjectRoot`.
5. Select **Refresh** and wait for completion.
6. Inspect **Transform data** for query errors, warning icons or unexpected source dependencies.
7. Inspect **Model view** for missing tables, ambiguous paths or relationship warnings.
8. Inspect the `Measures` table for DAX error indicators.

Expected unfiltered dataset evidence after a successful refresh:

| Metric | Expected value |
|---|---:|
| Total Claims | 75,000 |
| Open Claims | 9,331 |
| Total Incurred | R9,053,960,963.10 |
| Total Paid | R7,214,532,220.11 |
| Outstanding Reserve | R1,839,428,742.99 |
| Average Severity | R143,506.93 |
| Average Settlement Days | 45.1 |
| Median Settlement Days | 39 |
| P90 Settlement Days | 85 |
| SLA Compliance | 61.4% |
| High/Critical Risk Claims | 9,334 |

These are deterministic portfolio expectations, not runtime results. A mismatch must be investigated rather than overwritten.

## 3. Validate the model

- [ ] Confirm all 15 model tables load.
- [ ] Confirm `DimDate` is recognized as the date table using `DimDate[Date]`.
- [ ] Confirm the loss-date relationship is active.
- [ ] Confirm report-date and settlement-date relationships remain inactive.
- [ ] Confirm all other dimensional filters are single-direction.
- [ ] Confirm no ambiguous relationship warning appears.
- [ ] Confirm month, status, severity and risk labels sort by their governed order columns.
- [ ] Confirm hidden keys and technical fields do not clutter report authoring.
- [ ] Confirm Rand, percentage, count and date formats render as intended.
- [ ] Test the `Executive` and `Regional Manager` roles with **View as**.

## 4. Verify every report page

For each page, inspect the title, grid alignment, margins, card consistency, text overflow, labels, legends, axes, number formats, blank states and disclosure text.

| # | Page | Render | Formatting | Filters | Interactions | Evidence |
|---:|---|---|---|---|---|---|
| 1 | Executive Claims Overview | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 2 | Claims Operations | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 3 | Risk & Review Intelligence | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 4 | Financial Performance | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 5 | Regional Intelligence | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 6 | Handler Performance | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 7 | Root Cause Analysis | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |
| 8 | Data Quality | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | MANUAL REVIEW | Add screenshot path |

## 5. Test filter contexts

Test each scenario and verify that KPI cards, charts and titles respond consistently.

- [ ] Date: full period
- [ ] Date: 2024, 2025 and 2026 individually
- [ ] Date: one selected month
- [ ] Date: multi-month range crossing a year boundary
- [ ] Product: Motor
- [ ] Product: Agricultural
- [ ] Region: at least three provinces, including one lower-volume province
- [ ] Claim type: one common and one lower-volume category
- [ ] Risk: Low, Medium, High and Critical
- [ ] Status: open lifecycle states and Settled
- [ ] Multiple slicers together to test intersection behavior
- [ ] Clear filters and confirm the unfiltered portfolio baseline returns

## 6. Test field and what-if parameters

- [ ] Switch the analysis metric through Total Incurred, Average Severity, Settlement Days, SLA Compliance and Fraud Referral Rate.
- [ ] Confirm visual titles and formats remain appropriate after switching.
- [ ] Set investigation capacity to 5%, 10%, 15% and 20%.
- [ ] Confirm Claims Selected, Synthetic Targets Captured, Review Precision, Synthetic Target Recall, Non-Target Review Rate and Lift update.

Expected 10% capacity checkpoint:

| Metric | Expected value |
|---|---:|
| Claims Selected | 7,500 |
| Synthetic Targets Captured | 1,132 |
| Review Precision | 15.1% |
| Synthetic Target Recall | 16.9% |
| Non-Target Review Rate | 84.9% |
| Lift vs Random Review | 1.69× |

## 7. Test report interactions

- [ ] Cross-filter from each major chart and verify related visuals respond.
- [ ] Confirm chart selections do not unexpectedly clear required slicers.
- [ ] Test every navigation button and page tab.
- [ ] Test configured bookmarks and record any page where none are implemented.
- [ ] Test the reset-filter action and confirm the intended default state.
- [ ] Test report tooltips for correct row and filter context.
- [ ] Test drill-through destinations and the Back action.
- [ ] Test blank/low-volume selections for readable empty states.
- [ ] Inspect phone layouts and record whether they are configured or still required.
- [ ] Use **View as** to demonstrate conceptual RLS behavior.

Do not mark an interaction PASS merely because related source metadata exists.

## 8. Runtime-test priority measures

Test totals and at least two filtered contexts for:

- Total Claims, Open Claims
- Total Incurred, Total Paid, Outstanding Reserve
- Average Severity, Median Severity
- Average, Median and P90 Settlement Days
- SLA Compliance %, Reopen Rate %, Complaint Rate %
- High Risk Claims %
- Claims YoY %, Incurred YoY %, Severity YoY %
- Rolling 12M Claims, Rolling 12M Incurred
- 30+ Day Open Claims, 60+ Day Open Claims, Backlog %
- All review-capacity measures

Check totals, subtotals, blanks, prior-year boundaries, inactive-date behavior and divide-by-zero handling.

## 9. Capture genuine screenshots

Only after a page has rendered and passed its checks:

1. Reset filters to a clean, useful state.
2. Use a consistent 16:9 viewport, preferably 1600×900.
3. Hide panes or application chrome that distract from the report where practical.
4. Exclude notifications, usernames, confidential paths and unrelated applications.
5. Save genuine Power BI Desktop renders as:

```text
assets/powerbi/01-executive-overview.png
assets/powerbi/02-claims-operations.png
assets/powerbi/03-risk-review-intelligence.png
assets/powerbi/04-financial-performance.png
assets/powerbi/05-regional-intelligence.png
assets/powerbi/06-handler-performance.png
assets/powerbi/07-root-cause-analysis.png
assets/powerbi/08-data-quality.png
```

Optionally derive `assets/powerbi/hero-executive-dashboard.png` from the genuine Executive Overview capture. Do not create these files from the existing design mockups.

## 10. Close the evidence record

- [ ] Enter Desktop version, test date and tester in the runtime-verification document.
- [ ] Change only genuinely completed results from MANUAL REVIEW to PASS or FAIL.
- [ ] Link every screenshot or supporting note.
- [ ] Record any issue, correction and retest outcome.
- [ ] Rerun automated QA after committing verified evidence.
- [ ] Replace the README's pending-runtime wording only when the evidence table supports it.

