"""
Dataset Generator: A/B Test – E-Commerce Landing Page Optimization
Simulates a realistic 4-week experiment on an online platform.
"""

import pandas as pd
import numpy as np

np.random.seed(42)

N = 10000  # total users

user_ids = range(1, N + 1)
groups = np.random.choice(['control', 'treatment'], size=N, p=[0.5, 0.5])
devices = np.random.choice(['desktop', 'mobile', 'tablet'], size=N, p=[0.45, 0.45, 0.10])
countries = np.random.choice(['DE', 'AT', 'CH'], size=N, p=[0.70, 0.20, 0.10])

# Simulate experiment over 4 weeks
dates = pd.date_range('2024-01-08', '2024-02-04', periods=N).to_numpy().copy()
np.random.shuffle(dates)

# Session duration (seconds) — treatment page is slightly more engaging
session_duration = np.where(
    groups == 'treatment',
    np.random.normal(210, 60, N),   # treatment: avg 3.5 min
    np.random.normal(180, 65, N)    # control:   avg 3.0 min
).clip(10, 900)

# Pages viewed per session
pages_viewed = np.where(
    groups == 'treatment',
    np.random.poisson(3.8, N),
    np.random.poisson(3.2, N)
).clip(1, 20)

# Click-through rate (clicked CTA button)
ctr_prob = np.where(groups == 'treatment', 0.38, 0.30)
ctr_prob = np.where(devices == 'mobile', ctr_prob * 0.90, ctr_prob)  # mobile slightly lower
clicked = np.random.binomial(1, ctr_prob)

# Conversion (purchase) — only possible if clicked
conv_base = np.where(groups == 'treatment', 0.12, 0.09)
converted = np.where(clicked == 1, np.random.binomial(1, conv_base), 0)

# Revenue (only for converted users)
revenue = np.where(converted == 1, np.random.normal(49.90, 18.0, N).clip(9.99, 199.99), 0.0)

df = pd.DataFrame({
    'user_id': user_ids,
    'date': pd.to_datetime(dates).date,
    'group': groups,
    'device': devices,
    'country': countries,
    'session_duration_sec': session_duration.round(0).astype(int),
    'pages_viewed': pages_viewed,
    'clicked_cta': clicked,
    'converted': converted,
    'revenue_eur': revenue.round(2)
})

df.to_csv('/home/claude/ab_project/ab_test_data.csv', index=False)
print(f"Dataset saved: {len(df)} rows")
print(df.groupby('group')[['clicked_cta','converted','revenue_eur']].mean().round(4))
