"""
Skill-level ASR (Attack Success Rate = accept rate) profiling.
- Per-skill ASR aggregated over 9 cells (3 cond × 3 model) and per-condition.
- Group comparison: high-ASR (=1.0) vs low-ASR (<0.7) skill features.
- Continuous correlation between skill features and ASR.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pointbiserialr, mannwhitneyu

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "dataset.csv")

NUMERIC_FEATS = [
    "n_env_vars", "n_unique_env_vars",
    "has_password_var", "has_apikey_var", "has_token_var", "has_oauth_vars",
    "n_capabilities", "n_lines", "n_chars",
    "has_version", "has_author",
    "mentions_2fa", "mentions_imessage",
]

# Skill-level ASR (overall + per-condition)
overall = df.groupby("skill_name")["accept"].mean().rename("ASR_overall")
per_cond = df.pivot_table(index="skill_name", columns="condition", values="accept", aggfunc="mean")
per_cond.columns = [f"ASR_{c}" for c in per_cond.columns]

# Skill features (deduplicated)
feat_cols = NUMERIC_FEATS + ["category", "sensitivity"]
skill_feat = df.drop_duplicates("skill_name").set_index("skill_name")[feat_cols]
profile = skill_feat.join(overall).join(per_cond).sort_values("ASR_overall", ascending=False)
profile.to_csv(HERE / "skill_asr_profile.csv")

print("="*72)
print(f"== Per-skill ASR distribution (n={len(profile)})")
print("="*72)
print(profile["ASR_overall"].describe().round(3))
print(f"\nASR == 1.000 : {(profile['ASR_overall']==1.0).sum()} skills")
print(f"ASR  > 0.95 : {(profile['ASR_overall']>0.95).sum()} skills")
print(f"ASR  < 0.70 : {(profile['ASR_overall']<0.70).sum()} skills")

# Continuous correlation
print("\n" + "="*72)
print("== Continuous correlation: feature ↔ ASR_overall (point-biserial / Pearson)")
print("="*72)
results = []
for f in NUMERIC_FEATS:
    if profile[f].nunique() < 2:
        continue
    if profile[f].nunique() == 2:
        r, p = pointbiserialr(profile[f], profile["ASR_overall"])
    else:
        r = profile[f].corr(profile["ASR_overall"])
        # rough p via abs(r) only — informational only
        p = float("nan")
    results.append((f, r, p))
results.sort(key=lambda x: -abs(x[1]))
print(f"  {'feature':<22} {'r':>7} {'p':>10}")
for f, r, p in results:
    print(f"  {f:<22} {r:>+7.3f} {p:>10.4f}")

# Group comparison: high-ASR (==1.0) vs low-ASR (<0.7)
high = profile[profile["ASR_overall"] == 1.0]
low = profile[profile["ASR_overall"] < 0.7]
print("\n" + "="*72)
print(f"== Group comparison: ASR=1.0 (n={len(high)}) vs ASR<0.7 (n={len(low)})")
print("="*72)
print(f"  {'feature':<22} {'mean(high)':>12} {'mean(low)':>12} {'Δ':>8}  MWU-p")
for f in NUMERIC_FEATS:
    mh = high[f].mean()
    ml = low[f].mean()
    if high[f].nunique() < 2 and low[f].nunique() < 2:
        p = float("nan")
    else:
        try:
            _, p = mannwhitneyu(high[f], low[f], alternative="two-sided")
        except ValueError:
            p = float("nan")
    flag = " ←" if not np.isnan(p) and p < 0.05 else ""
    print(f"  {f:<22} {mh:>12.3f} {ml:>12.3f} {mh-ml:>+8.3f}  {p:>.4f}{flag}")

# Category breakdown
print("\n  Category distribution:")
print("    high (ASR=1.0):", high["category"].value_counts().to_dict())
print("    low  (ASR<0.7):", low["category"].value_counts().to_dict())

print("\n  Sensitivity tier distribution:")
print("    high (ASR=1.0):", high["sensitivity"].value_counts().to_dict())
print("    low  (ASR<0.7):", low["sensitivity"].value_counts().to_dict())

# Skill name lists
print("\n" + "="*72)
print("== Top 20 highest-ASR skills (full attack success)")
print("="*72)
top = profile.head(30)[["category", "sensitivity", "ASR_overall", "ASR_listing-only", "ASR_trust-badge", "ASR_task-driven", "n_env_vars", "has_password_var", "has_apikey_var", "n_lines"]]
print(top.to_string())

print("\n" + "="*72)
print("== Bottom 15 lowest-ASR skills (most resistant)")
print("="*72)
bot = profile.tail(15)[["category", "sensitivity", "ASR_overall", "ASR_listing-only", "ASR_trust-badge", "ASR_task-driven", "n_env_vars", "has_password_var", "has_apikey_var", "n_lines"]]
print(bot.to_string())
