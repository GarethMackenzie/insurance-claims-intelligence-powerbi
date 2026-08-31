# Power BI Desktop setup

## Open and refresh

1. Install a current Power BI Desktop release that supports PBIP, PBIR and TMDL preview features.
2. Clone or unzip the repository.
3. Regenerate the data if desired using the commands in the root README.
4. Open `InsuranceClaimsIntelligence.pbip`.
5. If the repository moved, edit the `pProjectRoot` Power Query parameter to the new absolute repository path.
6. Import `theme/insurance-intelligence-theme.json` if Desktop does not automatically retain an external theme reference.
7. Mark `DimDate[Date]` as the date table and refresh.
8. Inspect relationships, roles and the 79-measure `Measures` table before publishing.

## Desktop-only finishing checks

Power BI Desktop was not available in the build environment. The PBIR source contains all eight pages, bound KPI/chart definitions, slicers and disclosure text. In Desktop, verify visual role mappings for the installed report schema, then configure or confirm bookmarks, synced slicers, reset-filter actions, report-tooltip targets, provincial drill-through and phone layouts. These interaction states require a rendering host and are not claimed as runtime-tested here.

## Save as PBIX

After a successful refresh and interaction check, use **File → Save a copy** and select `.pbix` if a binary distribution is needed. This repository intentionally does not fabricate or commit a PBIX.
