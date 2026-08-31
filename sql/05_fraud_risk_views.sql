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
