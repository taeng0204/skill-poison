"""
Track B — Micro discovery: within each condition, which skill-level features
predict refuse/accept? Use shallow decision tree + permutation importance.
Caveat: 255 samples per condition, ~10 features → low statistical power.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, cross_val_score

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "dataset.csv")

NUMERIC_FEATS = [
    "n_env_vars", "n_unique_env_vars",
    "has_password_var", "has_apikey_var", "has_token_var", "has_oauth_vars",
    "n_capabilities", "n_lines", "has_version", "has_author",
    "mentions_2fa", "mentions_imessage",
]

# encode sensitivity (high=2, medium=1, low=0)
sens_map = {"high": 2, "medium": 1, "low": 0, "unknown": -1}
df["sensitivity_score"] = df["sensitivity"].map(sens_map)
NUMERIC_FEATS.append("sensitivity_score")

# encode model as numeric for the within-condition view
model_map = {"qwen2.5:7b": 0, "qwen3:8b": 1, "llama3.1:8b": 2}
df["model_id"] = df["model"].map(model_map)


def analyze_condition(cond):
    sub = df[df["condition"] == cond].copy()
    print(f"\n{'='*72}\n== Condition: {cond}  (n={len(sub)},  refuse={int((1-sub['accept']).sum())})\n{'='*72}")

    if sub["accept"].nunique() < 2:
        print("  Only one class — skipping (no variance)")
        return
    if (1 - sub["accept"]).sum() < 5:
        print(f"  Only {int((1-sub['accept']).sum())} refuse cases — degenerate, results unreliable")

    feats = NUMERIC_FEATS + ["model_id"]
    X = sub[feats].fillna(-1)
    y = (1 - sub["accept"]).astype(int)  # predict REFUSE (the rare/interesting class)

    # Shallow tree
    tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, class_weight="balanced", random_state=0)
    tree.fit(X, y)

    # CV score (be honest about overfit risk)
    if y.sum() >= 5 and (len(y) - y.sum()) >= 5:
        cv = cross_val_score(
            DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, class_weight="balanced", random_state=0),
            X, y, cv=StratifiedKFold(n_splits=min(5, y.sum()), shuffle=True, random_state=0),
            scoring="balanced_accuracy"
        )
        print(f"  CV balanced accuracy (predicting REFUSE): {cv.mean():.3f} ± {cv.std():.3f}")

    # Permutation importance
    perm = permutation_importance(tree, X, y, n_repeats=20, random_state=0, scoring="balanced_accuracy")
    imp = pd.Series(perm.importances_mean, index=feats).sort_values(ascending=False)

    print("\n  Top permutation importances:")
    for name, val in imp.head(8).items():
        print(f"    {val:+.4f}  {name}")

    # Refuse rate by service category (sanity check on what the tree picks up)
    print("\n  Refuse rate by category (top categories with refusals):")
    cat_refuse = sub.groupby("category")["accept"].agg(["count", lambda x: (1 - x).sum(), "mean"])
    cat_refuse.columns = ["n", "n_refuse", "accept_rate"]
    cat_refuse = cat_refuse[cat_refuse["n_refuse"] > 0].sort_values("accept_rate")
    print(cat_refuse.to_string())

    print("\n  Refuse rate by sensitivity tier:")
    print(sub.groupby("sensitivity")["accept"].agg(["count", lambda x: (1 - x).sum(), "mean"]).rename(
        columns={"<lambda_0>": "n_refuse", "mean": "accept_rate"}).to_string())


for cond in ["listing-only", "trust-badge", "task-driven"]:
    analyze_condition(cond)


# Cross-condition: which 27 skills are universally accepted, which 4 are universally refused?
print(f"\n{'='*72}\n== Cross-condition: universally accept vs frequently refuse\n{'='*72}")
pivot = df.groupby("skill_name")["accept"].agg(["mean", "sum", "count"]).rename(columns={"mean":"accept_rate","sum":"n_accept","count":"n_total"})
feat_lookup = df.drop_duplicates("skill_name").set_index("skill_name")[NUMERIC_FEATS + ["category", "sensitivity"]]
pivot = pivot.join(feat_lookup)

print("\n-- Always-accept (accept_rate=1.0):", int((pivot["accept_rate"]==1.0).sum()), "skills")
print("   sensitivity dist:", pivot[pivot["accept_rate"]==1.0]["sensitivity"].value_counts().to_dict())

print("\n-- Frequently-refused (accept_rate < 0.7), sorted:")
freq_refuse = pivot[pivot["accept_rate"] < 0.7].sort_values("accept_rate")
print(freq_refuse[["accept_rate","n_accept","n_total","category","sensitivity"]].to_string())
