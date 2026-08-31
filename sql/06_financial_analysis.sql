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
