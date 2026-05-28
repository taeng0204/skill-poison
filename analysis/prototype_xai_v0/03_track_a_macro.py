"""
Track A — Macro causal: estimate the average effect of condition macro-features
(trust_badge, task_context) and model on accept probability.

Reference condition: listing-only (setup_visible=0, trust_badge=0, task_context=0).
Reference model: qwen2.5:7b.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).parent
df = pd.read_csv(HERE / "dataset.csv")

# Encode model as one-hot, drop reference
model_dummies = pd.get_dummies(df["model"], prefix="model", drop_first=False)
ref_model_col = "model_qwen2.5:7b"
model_dummies = model_dummies.drop(columns=[ref_model_col])

# Build feature matrix
X = pd.concat([
    df[["trust_badge", "task_context"]].astype(int),
    model_dummies.astype(int),
], axis=1)

# Add interactions: condition × model
for cond_col in ["trust_badge", "task_context"]:
    for m_col in model_dummies.columns:
        X[f"{cond_col}__x__{m_col}"] = X[cond_col] * X[m_col]

y = df["accept"].astype(int)

clf = LogisticRegression(C=1e6, max_iter=2000, solver="lbfgs")
clf.fit(X, y)

coefs = pd.Series(clf.coef_[0], index=X.columns)
intercept = clf.intercept_[0]

print(f"Intercept (logit): {intercept:+.3f}  → baseline accept p = {1/(1+np.exp(-intercept)):.3f}")
print("  (baseline = listing-only × qwen2.5:7b)\n")

print("=== Coefficients (logit scale, change in log-odds) ===")
for name, val in coefs.sort_values(ascending=False).items():
    odds = np.exp(val)
    print(f"  {val:+7.3f}  (×{odds:7.2f} odds)  {name}")

# Interpretable predicted probabilities for each cell
print("\n=== Model-predicted accept probability per cell ===")
combos = []
for cond_label, cond_vals in [
    ("listing-only", (0, 0)),
    ("trust-badge",  (1, 0)),
    ("task-driven",  (0, 1)),
]:
    for model in ["qwen2.5:7b", "qwen3:8b", "llama3.1:8b"]:
        row = {c: 0 for c in X.columns}
        row["trust_badge"], row["task_context"] = cond_vals
        if model != "qwen2.5:7b":
            row[f"model_{model}"] = 1
        # interactions
        for cond_col in ["trust_badge", "task_context"]:
            for m_col in model_dummies.columns:
                row[f"{cond_col}__x__{m_col}"] = row[cond_col] * row[m_col]
        p = clf.predict_proba(pd.DataFrame([row]))[0, 1]
        combos.append((cond_label, model, p, df[(df["condition"]==cond_label)&(df["model"]==model)]["accept"].mean()))

print(f"  {'condition':<14} {'model':<14} {'predicted':>10} {'observed':>10}")
for c, m, p, o in combos:
    print(f"  {c:<14} {m:<14} {p:>10.3f} {o:>10.3f}")

# Average treatment effects (observed, not model — simpler & honest)
print("\n=== Average Treatment Effect (observed, vs listing-only baseline) ===")
base = df[df["condition"]=="listing-only"]["accept"].mean()
for cond in ["trust-badge", "task-driven"]:
    p = df[df["condition"]==cond]["accept"].mean()
    print(f"  {cond:<14} ATE = {p - base:+.3f}  ({base:.3f} → {p:.3f})")

print("\n=== ATE by model (vs listing-only of same model) ===")
for model in ["qwen2.5:7b", "qwen3:8b", "llama3.1:8b"]:
    base = df[(df["condition"]=="listing-only") & (df["model"]==model)]["accept"].mean()
    print(f"  -- {model} (baseline {base:.3f})")
    for cond in ["trust-badge", "task-driven"]:
        p = df[(df["condition"]==cond) & (df["model"]==model)]["accept"].mean()
        print(f"      {cond:<14} ATE {p - base:+.3f}  ({base:.3f} → {p:.3f})")
