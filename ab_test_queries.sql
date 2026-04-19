-- ============================================================
-- A/B Test SQL Analysis: Landing Page Optimization
-- Author: Ghaziafa Nawaz
-- Database: PostgreSQL-compatible
-- Table: ab_test_data (user_id, date, group, device, country,
--        session_duration_sec, pages_viewed, clicked_cta,
--        converted, revenue_eur)
-- ============================================================


-- ─────────────────────────────────────────────────────────────
-- 1. SAMPLE CHECK: Ensure balanced group distribution
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    COUNT(*)                            AS users,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM ab_test_data
GROUP BY "group";


-- ─────────────────────────────────────────────────────────────
-- 2. CORE KPI SUMMARY BY GROUP
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    COUNT(*)                                                  AS total_users,
    SUM(clicked_cta)                                          AS total_clicks,
    ROUND(AVG(clicked_cta::FLOAT) * 100, 2)                  AS ctr_pct,
    SUM(converted)                                            AS total_conversions,
    ROUND(AVG(converted::FLOAT) * 100, 2)                    AS conversion_rate_pct,
    ROUND(AVG(session_duration_sec), 1)                       AS avg_session_sec,
    ROUND(AVG(pages_viewed), 2)                               AS avg_pages_viewed,
    ROUND(SUM(revenue_eur), 2)                                AS total_revenue_eur,
    ROUND(AVG(revenue_eur), 4)                                AS avg_revenue_per_user
FROM ab_test_data
GROUP BY "group"
ORDER BY "group";


-- ─────────────────────────────────────────────────────────────
-- 3. CONVERSION FUNNEL (Visited → Clicked → Converted)
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    COUNT(*)                            AS visited,
    SUM(clicked_cta)                    AS clicked,
    SUM(converted)                      AS converted,
    ROUND(SUM(clicked_cta) * 100.0 / COUNT(*), 2)    AS click_rate_pct,
    ROUND(SUM(converted) * 100.0 / NULLIF(SUM(clicked_cta), 0), 2) AS click_to_conv_pct,
    ROUND(SUM(converted) * 100.0 / COUNT(*), 2)      AS overall_conv_rate_pct
FROM ab_test_data
GROUP BY "group";


-- ─────────────────────────────────────────────────────────────
-- 4. SEGMENT ANALYSIS: CTR & Conversion by Device
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    device,
    COUNT(*)                                        AS users,
    ROUND(AVG(clicked_cta::FLOAT) * 100, 2)        AS ctr_pct,
    ROUND(AVG(converted::FLOAT) * 100, 2)          AS conversion_rate_pct,
    ROUND(AVG(revenue_eur), 4)                      AS avg_revenue_per_user
FROM ab_test_data
GROUP BY "group", device
ORDER BY "group", device;


-- ─────────────────────────────────────────────────────────────
-- 5. WEEKLY TREND: Conversion rate over time
-- ─────────────────────────────────────────────────────────────
SELECT
    DATE_TRUNC('week', date)            AS week_start,
    "group",
    COUNT(*)                            AS users,
    ROUND(AVG(converted::FLOAT) * 100, 2)  AS conversion_rate_pct,
    ROUND(SUM(revenue_eur), 2)          AS weekly_revenue
FROM ab_test_data
GROUP BY DATE_TRUNC('week', date), "group"
ORDER BY week_start, "group";


-- ─────────────────────────────────────────────────────────────
-- 6. REVENUE ANALYSIS: Average order value (buyers only)
-- ─────────────────────────────────────────────────────────────
SELECT
    "group",
    COUNT(*)                            AS total_buyers,
    ROUND(AVG(revenue_eur), 2)          AS avg_order_value_eur,
    ROUND(MIN(revenue_eur), 2)          AS min_order_eur,
    ROUND(MAX(revenue_eur), 2)          AS max_order_eur,
    ROUND(PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY revenue_eur), 2) AS median_order_eur,
    ROUND(SUM(revenue_eur), 2)          AS total_revenue_eur
FROM ab_test_data
WHERE converted = 1
GROUP BY "group";


-- ─────────────────────────────────────────────────────────────
-- 7. COUNTRY BREAKDOWN
-- ─────────────────────────────────────────────────────────────
SELECT
    country,
    "group",
    COUNT(*)                                        AS users,
    ROUND(AVG(converted::FLOAT) * 100, 2)          AS conversion_rate_pct,
    ROUND(SUM(revenue_eur), 2)                      AS total_revenue_eur
FROM ab_test_data
GROUP BY country, "group"
ORDER BY country, "group";


-- ─────────────────────────────────────────────────────────────
-- 8. LIFT CALCULATION (CTE approach)
-- ─────────────────────────────────────────────────────────────
WITH metrics AS (
    SELECT
        "group",
        ROUND(AVG(clicked_cta::FLOAT), 4)   AS ctr,
        ROUND(AVG(converted::FLOAT), 4)     AS cvr,
        ROUND(AVG(revenue_eur), 4)          AS arpu
    FROM ab_test_data
    GROUP BY "group"
),
control AS (SELECT * FROM metrics WHERE "group" = 'control'),
treatment AS (SELECT * FROM metrics WHERE "group" = 'treatment')
SELECT
    ROUND((t.ctr  - c.ctr)  / c.ctr  * 100, 1)  AS ctr_lift_pct,
    ROUND((t.cvr  - c.cvr)  / c.cvr  * 100, 1)  AS conversion_lift_pct,
    ROUND((t.arpu - c.arpu) / c.arpu * 100, 1)  AS revenue_lift_pct
FROM control c, treatment t;
