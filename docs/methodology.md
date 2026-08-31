# Methodology

## Synthetic portfolio generation

The fixed NumPy seed is `20260831`. Loss dates span 2024-01-01 through 2026-08-31, with a modest volume trend and seasonal weather uplift. Product, claim type, province and channel are sampled from documented conditional distributions. Amounts use claim-type baselines, portfolio and regional factors, severity inflation, weather seasonality and a capped log-normal distribution.

Operational fields are correlated by construction. Complexity rises with amount and selected claim types. Missing documentation adds assessment and decision delay. Two simulated backlog windows add cycle time. Large or complex claims generally settle more slowly and carry larger simplified case reserves. Complaints and reopening are more likely when SLA or complexity signals are adverse.

The risk score combines reporting delay, prior claims, theft/fire indicators, large-loss status, channel, policy tenure and small regional effects, plus noise. `Synthetic_Fraud_Target_Flag` is a clearly named seeded demonstration outcome used to calculate review precision, synthetic-target recall and lift. Neither field represents a real fraud model or confirms fraud.

## Quality challenge

Exactly 2,150 controlled issue events are seeded across a still-usable raw extract. Each event has a stable raw-row identifier, correction value and resolution. Validation proves that the observed raw condition matches the manifest before the clean build applies it. The later copy of each duplicate claim is removed.

## Analytical stance

Findings are calculated only after the clean dataset exists. They describe association and concentration in a synthetic portfolio. No causal, actuarial, production or workplace-performance claim is made.
