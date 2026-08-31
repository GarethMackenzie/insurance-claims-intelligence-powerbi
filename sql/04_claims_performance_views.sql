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
