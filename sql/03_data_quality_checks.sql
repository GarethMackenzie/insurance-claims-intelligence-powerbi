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
