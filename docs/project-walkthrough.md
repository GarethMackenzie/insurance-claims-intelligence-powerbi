# Recruiter project walkthrough

This is a natural 60–90 second interview explanation and future screen-recording script. No walkthrough video is claimed or included because Power BI Desktop recording was unavailable in the current environment.

## 0–10 seconds — business problem

“Claims leaders need one reliable view of volume, financial exposure, service levels, backlog and constrained risk-review capacity. This project shows how I would turn those questions into governed executive decision support.”

**Suggested shot:** repository title, synthetic-data disclosure and Executive Claims Overview.

## 10–25 seconds — architecture and data

“The portfolio starts with 75,000 deterministic synthetic claims. Python creates a controlled raw-data challenge, validates every seeded issue and builds a clean star schema. Power Query loads the governed extracts, while PBIP, PBIR and TMDL keep the report and semantic model inspectable in source control.”

**Suggested shot:** architecture diagram followed by the star-schema diagram.

## 25–45 seconds — executive dashboard

“The executive page brings together claim volume, incurred exposure, paid amounts, reserve, severity, settlement time, SLA and high-risk referrals. The purpose is to identify where pressure is building and decide what deserves investigation.”

**Suggested shot:** genuine Executive Claims Overview render once available.

## 45–60 seconds — operational and risk analytics

“The supporting pages move from backlog and settlement performance into financial, regional and root-cause views. The review-capacity simulator demonstrates how a team could prioritize a limited queue at 5%, 10%, 15% or 20% capacity. The score prioritizes human review; it does not determine fraud or automate a claim decision.”

**Suggested shot:** Claims Operations, Risk & Review Intelligence, then Root Cause Analysis.

## 60–75 seconds — engineering depth

“Under the report are 79 explicit DAX measures, single-direction relationships, role-playing dates, reusable M, six SQL modules and automated checks for data grain, financial reconciliation, semantic structure, privacy and repository integrity.”

**Suggested shot:** TMDL measure source, Power Query, SQL and the QA report.

## 75–90 seconds — takeaway

“This project demonstrates how I move from raw insurance claims data through governed transformation, semantic modelling and DAX into executive decision support—while keeping the work reproducible, privacy-safe and honest about what has and has not been runtime verified.”

**Suggested shot:** GitHub Actions PASS and the responsible-analytics limitation.

## Recording shot list

1. Repository opening and synthetic-data disclosure
2. Architecture diagram
3. Star schema
4. Executive Claims Overview
5. Claims Operations
6. Risk & Review capacity parameter
7. Root Cause Analysis
8. TMDL/DAX source
9. QA report and successful GitHub Actions run

Use genuine Power BI Desktop renders for report shots. Until those exist, this document is a narration and capture plan—not evidence of a completed video.
