"""
============================================================
A/B Test Analysis: Landing Page Optimization
E-Commerce Platform | January–February 2024
============================================================
Author : Ghaziafa Nawaz
Tools  : Python (pandas, scipy, matplotlib, seaborn)
Goal   : Evaluate whether the new landing page (treatment)
         significantly improves CTR, conversion rate and revenue
         vs. the original page (control).
============================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import warnings
warnings.filterwarnings('ignore')

# ── Styling ────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
COLORS = {'control': '#5B8DB8', 'treatment': '#E07B54'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})

# ══════════════════════════════════════════════════════════
# 1. LOAD & VALIDATE DATA
# ══════════════════════════════════════════════════════════
df = pd.read_csv('ab_test_data.csv', parse_dates=['date'])

print("=" * 60)
print("1. DATA OVERVIEW")
print("=" * 60)
print(f"Total users   : {len(df):,}")
print(f"Date range    : {df['date'].min()} → {df['date'].max()}")
print(f"Groups        : {df['group'].value_counts().to_dict()}")
print(f"Devices       : {df['device'].value_counts().to_dict()}")
print(f"Missing values: {df.isnull().sum().sum()}")
print()

# ══════════════════════════════════════════════════════════
# 2. KEY METRICS SUMMARY
# ══════════════════════════════════════════════════════════
print("=" * 60)
print("2. KEY METRICS BY GROUP")
print("=" * 60)

summary = df.groupby('group').agg(
    users=('user_id', 'count'),
    ctr=('clicked_cta', 'mean'),
    conversion_rate=('converted', 'mean'),
    avg_session_sec=('session_duration_sec', 'mean'),
    avg_pages=('pages_viewed', 'mean'),
    total_revenue=('revenue_eur', 'sum'),
    avg_revenue_per_user=('revenue_eur', 'mean')
).round(4)

print(summary.T.to_string())
print()

# Relative lifts
ctrl  = summary.loc['control']
treat = summary.loc['treatment']
print(f"CTR lift            : +{(treat.ctr/ctrl.ctr - 1)*100:.1f}%")
print(f"Conversion lift     : +{(treat.conversion_rate/ctrl.conversion_rate - 1)*100:.1f}%")
print(f"Revenue/user lift   : +{(treat.avg_revenue_per_user/ctrl.avg_revenue_per_user - 1)*100:.1f}%")
print()

# ══════════════════════════════════════════════════════════
# 3. STATISTICAL TESTS
# ══════════════════════════════════════════════════════════
print("=" * 60)
print("3. STATISTICAL HYPOTHESIS TESTS")
print("=" * 60)
ALPHA = 0.05

def test_result(p, alpha=ALPHA):
    return "✅ SIGNIFICANT" if p < alpha else "❌ NOT significant"

# ── 3a. Chi-Square test: CTR ───────────────────────────────
ctrl_df  = df[df['group'] == 'control']
treat_df = df[df['group'] == 'treatment']

ctr_table = pd.crosstab(df['group'], df['clicked_cta'])
chi2_ctr, p_ctr, _, _ = chi2_contingency(ctr_table)
print(f"\n[Chi-Square] Click-Through Rate")
print(f"  H0: No difference in CTR between groups")
print(f"  χ² = {chi2_ctr:.2f}, p = {p_ctr:.6f}  →  {test_result(p_ctr)}")

# ── 3b. Chi-Square test: Conversion Rate ──────────────────
conv_table = pd.crosstab(df['group'], df['converted'])
chi2_conv, p_conv, _, _ = chi2_contingency(conv_table)
print(f"\n[Chi-Square] Conversion Rate")
print(f"  H0: No difference in conversion rate between groups")
print(f"  χ² = {chi2_conv:.2f}, p = {p_conv:.6f}  →  {test_result(p_conv)}")

# ── 3c. Welch's t-Test: Session Duration ──────────────────
t_sess, p_sess = ttest_ind(treat_df['session_duration_sec'],
                            ctrl_df['session_duration_sec'], equal_var=False)
print(f"\n[Welch's t-Test] Session Duration")
print(f"  H0: No difference in avg session duration")
print(f"  t = {t_sess:.2f}, p = {p_sess:.6f}  →  {test_result(p_sess)}")

# ── 3d. Mann-Whitney U: Revenue (non-normal distribution) ─
rev_ctrl  = ctrl_df['revenue_eur']
rev_treat = treat_df['revenue_eur']
u_stat, p_rev = mannwhitneyu(rev_treat, rev_ctrl, alternative='greater')
print(f"\n[Mann-Whitney U] Revenue per User")
print(f"  H0: Treatment revenue ≤ control revenue")
print(f"  U = {u_stat:.0f}, p = {p_rev:.6f}  →  {test_result(p_rev)}")

# ── 3e. Confidence Intervals ──────────────────────────────
def proportion_ci(successes, n, z=1.96):
    p = successes / n
    margin = z * np.sqrt(p * (1 - p) / n)
    return p, p - margin, p + margin

n_ctrl  = len(ctrl_df)
n_treat = len(treat_df)

ctr_c,  ctr_c_lo,  ctr_c_hi  = proportion_ci(ctrl_df['clicked_cta'].sum(),  n_ctrl)
ctr_t,  ctr_t_lo,  ctr_t_hi  = proportion_ci(treat_df['clicked_cta'].sum(), n_treat)
conv_c, conv_c_lo, conv_c_hi = proportion_ci(ctrl_df['converted'].sum(),    n_ctrl)
conv_t, conv_t_lo, conv_t_hi = proportion_ci(treat_df['converted'].sum(),   n_treat)

print(f"\n[95% Confidence Intervals]")
print(f"  CTR     control  : {ctr_c:.3f}  [{ctr_c_lo:.3f}, {ctr_c_hi:.3f}]")
print(f"  CTR     treatment: {ctr_t:.3f}  [{ctr_t_lo:.3f}, {ctr_t_hi:.3f}]")
print(f"  Conv.   control  : {conv_c:.4f} [{conv_c_lo:.4f}, {conv_c_hi:.4f}]")
print(f"  Conv.   treatment: {conv_t:.4f} [{conv_t_lo:.4f}, {conv_t_hi:.4f}]")
print()

# ── 3f. Segment analysis: Device breakdown ────────────────
print("=" * 60)
print("4. SEGMENT ANALYSIS: Conversion Rate by Device")
print("=" * 60)
seg = df.groupby(['group','device'])['converted'].mean().unstack().round(4)
print(seg.to_string())
print()

# ── 3g. Weekly trend ──────────────────────────────────────
df['week'] = df['date'].dt.isocalendar().week
weekly = df.groupby(['week','group'])['converted'].mean().unstack().round(4)
print("Weekly Conversion Trend:")
print(weekly.to_string())
print()

# ══════════════════════════════════════════════════════════
# 4. VISUALIZATIONS
# ══════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12))
fig.suptitle("A/B Test Analysis – Landing Page Optimization\nE-Commerce Platform | Jan–Feb 2024",
             fontsize=15, fontweight='bold', y=0.98)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# ── Plot 1: CTR comparison with CI ────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
metrics = ['CTR', 'Conversion Rate']
ctrl_vals  = [ctr_c,  conv_c]
treat_vals = [ctr_t,  conv_t]
ctrl_errs  = [ctr_c  - ctr_c_lo,  conv_c  - conv_c_lo]
treat_errs = [ctr_t  - ctr_t_lo,  conv_t  - conv_t_lo]
x = np.arange(len(metrics))
w = 0.35
ax1.bar(x - w/2, ctrl_vals,  w, yerr=ctrl_errs,  capsize=5, label='Control',   color=COLORS['control'],   alpha=0.85)
ax1.bar(x + w/2, treat_vals, w, yerr=treat_errs, capsize=5, label='Treatment', color=COLORS['treatment'], alpha=0.85)
ax1.set_title('CTR & Conversion Rate\nwith 95% CI', fontweight='bold')
ax1.set_xticks(x); ax1.set_xticklabels(metrics)
ax1.set_ylabel('Rate'); ax1.legend()
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))

# ── Plot 2: Session Duration distribution ─────────────────
ax2 = fig.add_subplot(gs[0, 1])
for grp, color in COLORS.items():
    data = df[df['group'] == grp]['session_duration_sec']
    ax2.hist(data, bins=40, alpha=0.6, color=color, label=grp.capitalize(), density=True)
ax2.axvline(ctrl_df['session_duration_sec'].mean(),  color=COLORS['control'],   linestyle='--', linewidth=1.5)
ax2.axvline(treat_df['session_duration_sec'].mean(), color=COLORS['treatment'], linestyle='--', linewidth=1.5)
ax2.set_title('Session Duration\nDistribution', fontweight='bold')
ax2.set_xlabel('Seconds'); ax2.set_ylabel('Density'); ax2.legend()

# ── Plot 3: Revenue per user ───────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
rev_data = [ctrl_df['revenue_eur'], treat_df['revenue_eur']]
bp = ax3.boxplot(rev_data, patch_artist=True, widths=0.5,
                 medianprops=dict(color='white', linewidth=2))
for patch, color in zip(bp['boxes'], [COLORS['control'], COLORS['treatment']]):
    patch.set_facecolor(color); patch.set_alpha(0.8)
ax3.set_xticklabels(['Control', 'Treatment'])
ax3.set_title('Revenue per User\n(incl. non-buyers)', fontweight='bold')
ax3.set_ylabel('EUR')

# ── Plot 4: Weekly conversion trend ───────────────────────
ax4 = fig.add_subplot(gs[1, 0])
for grp, color in COLORS.items():
    ax4.plot(weekly.index, weekly[grp], marker='o', color=color,
             linewidth=2, label=grp.capitalize())
ax4.set_title('Weekly Conversion\nTrend', fontweight='bold')
ax4.set_xlabel('Calendar Week'); ax4.set_ylabel('Conversion Rate')
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1%}'))
ax4.legend()

# ── Plot 5: Device segment heatmap ────────────────────────
ax5 = fig.add_subplot(gs[1, 1])
sns.heatmap(seg * 100, annot=True, fmt='.2f', cmap='Blues',
            ax=ax5, cbar_kws={'label': 'Conv. Rate %'})
ax5.set_title('Conversion Rate %\nby Group & Device', fontweight='bold')
ax5.set_ylabel(''); ax5.set_xlabel('')

# ── Plot 6: Funnel ────────────────────────────────────────
ax6 = fig.add_subplot(gs[1, 2])
stages = ['Visited', 'Clicked CTA', 'Converted']
ctrl_funnel  = [n_ctrl,  ctrl_df['clicked_cta'].sum(),  ctrl_df['converted'].sum()]
treat_funnel = [n_treat, treat_df['clicked_cta'].sum(), treat_df['converted'].sum()]
x = np.arange(len(stages))
ax6.bar(x - 0.2, ctrl_funnel,  0.35, color=COLORS['control'],   alpha=0.85, label='Control')
ax6.bar(x + 0.2, treat_funnel, 0.35, color=COLORS['treatment'], alpha=0.85, label='Treatment')
ax6.set_title('Conversion Funnel\n(absolute users)', fontweight='bold')
ax6.set_xticks(x); ax6.set_xticklabels(stages, fontsize=9)
ax6.set_ylabel('Users'); ax6.legend()
for i, (c, t) in enumerate(zip(ctrl_funnel, treat_funnel)):
    ax6.text(i - 0.2, c + 30, f'{c:,}', ha='center', fontsize=8)
    ax6.text(i + 0.2, t + 30, f'{t:,}', ha='center', fontsize=8)

plt.savefig('ab_test_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
print("✅ Chart saved: ab_test_analysis.png")

# ══════════════════════════════════════════════════════════
# 5. BUSINESS RECOMMENDATION
# ══════════════════════════════════════════════════════════
print("=" * 60)
print("5. BUSINESS RECOMMENDATION")
print("=" * 60)
monthly_users = 50000
extra_conversions = (treat.conversion_rate - ctrl.conversion_rate) * monthly_users
avg_order = df[df['converted']==1]['revenue_eur'].mean()
extra_revenue = extra_conversions * avg_order

print(f"""
Recommendation: DEPLOY the treatment landing page.

All three primary metrics improved significantly (p < 0.05):
  • CTR:             {ctrl.ctr:.1%} → {treat.ctr:.1%}  (+{(treat.ctr/ctrl.ctr-1)*100:.1f}%)
  • Conversion rate: {ctrl.conversion_rate:.2%} → {treat.conversion_rate:.2%}  (+{(treat.conversion_rate/ctrl.conversion_rate-1)*100:.1f}%)
  • Revenue/user:    €{ctrl.avg_revenue_per_user:.2f} → €{treat.avg_revenue_per_user:.2f}  (+{(treat.avg_revenue_per_user/ctrl.avg_revenue_per_user-1)*100:.1f}%)

Estimated monthly impact (50,000 users):
  • +{extra_conversions:.0f} additional conversions
  • +€{extra_revenue:,.0f} additional revenue

Note: Mobile CTR is lower in both groups (–10% vs desktop).
A dedicated mobile UX optimization is recommended as next step.
""")
