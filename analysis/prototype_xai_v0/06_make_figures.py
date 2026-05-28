"""
Generate PNG figures summarizing XAI prototype v0 findings.
Outputs (in figs/):
  fig1_asr_distribution.png       — per-skill ASR histogram
  fig2_condition_model_heatmap.png — accept rate by condition × model
  fig3_macro_effects.png          — ATE per model per condition (grouped bar)
  fig4_category_asr.png           — ASR by service category (key finding)
  fig5_feature_importance.png     — permutation importance (task-driven)
  fig6_skill_ranking.png          — top/bottom skill ASR
  fig7_summary.png                — 2x2 multi-panel summary
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from sklearn.tree import DecisionTreeClassifier
from sklearn.inspection import permutation_importance

mpl.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "font.family": "DejaVu Sans",
})

HERE = Path(__file__).parent
FIGS = HERE / "figs"
FIGS.mkdir(exist_ok=True)

df = pd.read_csv(HERE / "dataset.csv")
profile = pd.read_csv(HERE / "skill_asr_profile.csv")

MODELS = ["qwen2.5:7b", "qwen3:8b", "llama3.1:8b"]
CONDS = ["listing-only", "trust-badge", "task-driven"]
COLOR_M = {"qwen2.5:7b": "#4C72B0", "qwen3:8b": "#DD8452", "llama3.1:8b": "#55A868"}
COLOR_C = {"listing-only": "#8172B2", "trust-badge": "#C44E52", "task-driven": "#937860"}

# ─────────────────────────────────────────────────────────────────
# Fig 1 — Per-skill ASR distribution
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
asr = profile["ASR_overall"]
bins = np.linspace(0.4, 1.0, 13)
ax.hist(asr, bins=bins, color="#4C72B0", edgecolor="white", alpha=0.85)
ax.axvline(asr.mean(), color="#C44E52", linestyle="--", lw=2, label=f"mean = {asr.mean():.3f}")
ax.axvline(0.7, color="black", linestyle=":", lw=1.5, alpha=0.5, label="ASR=0.70 cutoff")
ax.set_xlabel("Per-skill ASR (cross-condition × cross-model)")
ax.set_ylabel("# of skills")
ax.set_title(f"Skill ASR distribution (n=85, 27 skills at ASR=1.0)")
ax.legend()
ax.text(0.97, 0.95, "11 skills\n< 0.7", transform=ax.transAxes,
        ha="right", va="top", fontsize=9, color="#555",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3E0", edgecolor="#999"))
fig.tight_layout()
fig.savefig(FIGS / "fig1_asr_distribution.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 2 — Accept rate heatmap (condition × model)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6.5, 4))
heat = df.pivot_table(index="condition", columns="model", values="accept", aggfunc="mean")
heat = heat.reindex(index=CONDS, columns=MODELS)
im = ax.imshow(heat.values, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(MODELS)
ax.set_yticks(range(3)); ax.set_yticklabels(CONDS)
for i in range(3):
    for j in range(3):
        v = heat.values[i, j]
        ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                color="white" if v > 0.6 else "black", fontsize=11, fontweight="bold")
ax.set_title("Accept rate by condition × model  (255 decisions / cell)")
cbar = fig.colorbar(im, ax=ax, fraction=0.04)
cbar.set_label("Accept rate")
fig.tight_layout()
fig.savefig(FIGS / "fig2_condition_model_heatmap.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 3 — Macro ATE per model (vs listing-only baseline)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8.5, 4.5))
records = []
for m in MODELS:
    base = df[(df["model"] == m) & (df["condition"] == "listing-only")]["accept"].mean()
    for c in ["trust-badge", "task-driven"]:
        v = df[(df["model"] == m) & (df["condition"] == c)]["accept"].mean()
        records.append({"model": m, "condition": c, "ate": v - base})

ate = pd.DataFrame(records)
x = np.arange(2)
width = 0.27
for i, m in enumerate(MODELS):
    vals = ate[ate["model"] == m].set_index("condition").loc[["trust-badge", "task-driven"], "ate"]
    bars = ax.bar(x + (i - 1) * width, vals.values, width, color=COLOR_M[m], label=m, edgecolor="white")
    for b, v in zip(bars, vals.values):
        ax.text(b.get_x() + b.get_width()/2, v + (0.015 if v >= 0 else -0.025),
                f"{v:+.3f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=9)

ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(["+ trust-badge\n(vs listing-only)", "+ task-driven\n(vs listing-only)"])
ax.set_ylabel("Average Treatment Effect (Δ accept rate)")
ax.set_title("Macro effect of conditions per model")
ax.set_ylim(-0.6, 0.25)
ax.legend(loc="lower right")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "fig3_macro_effects.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 4 — Category × ASR (KEY finding)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.5))
cat_asr = profile.groupby("category").agg(
    asr=("ASR_overall", "mean"),
    n=("ASR_overall", "size"),
    sens=("sensitivity", "first"),
).sort_values("asr")

sens_color = {"high": "#C44E52", "medium": "#DD8452", "low": "#55A868", "unknown": "#888"}
colors = [sens_color[s] for s in cat_asr["sens"]]
bars = ax.barh(range(len(cat_asr)), cat_asr["asr"].values, color=colors, edgecolor="white")
ax.set_yticks(range(len(cat_asr)))
ax.set_yticklabels([f"{c}  (n={n})" for c, n in zip(cat_asr.index, cat_asr["n"])])
ax.set_xlabel("Mean ASR (cross-condition × cross-model)")
ax.set_title("ASR by service category — colored by our 'sensitivity' prior")
ax.axvline(profile["ASR_overall"].mean(), color="black", linestyle="--", lw=1, alpha=0.6,
           label=f"overall mean = {profile['ASR_overall'].mean():.3f}")
for b, v in zip(bars, cat_asr["asr"].values):
    ax.text(v + 0.005, b.get_y() + b.get_height()/2, f"{v:.2f}", va="center", fontsize=9)

# Legend for sensitivity colors
from matplotlib.patches import Patch
legend_handles = [
    Patch(facecolor=sens_color["high"], label="prior=HIGH (finance/health/...)"),
    Patch(facecolor=sens_color["medium"], label="prior=MEDIUM"),
    Patch(facecolor=sens_color["low"], label="prior=LOW (entertainment/...)"),
]
ax.legend(handles=legend_handles, loc="lower right")
ax.set_xlim(0, 1.1)
ax.text(0.02, 0.98,
        "* HIGH-prior categories (red) often outrank LOW (green):\n"
        "  finance/healthcare/insurance pass MORE than entertainment.\n"
        "  Model intuition is anti-aligned with our credential-density prior.",
        transform=ax.transAxes, va="top", ha="left", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF8E1", edgecolor="#999"))
fig.tight_layout()
fig.savefig(FIGS / "fig4_category_asr.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 5 — Feature importance (task-driven condition)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
sub = df[df["condition"] == "task-driven"].copy()
sens_map = {"high": 2, "medium": 1, "low": 0, "unknown": -1}
sub["sensitivity_score"] = sub["sensitivity"].map(sens_map)
model_map = {"qwen2.5:7b": 0, "qwen3:8b": 1, "llama3.1:8b": 2}
sub["model_id"] = sub["model"].map(model_map)

NUMERIC = [
    "n_env_vars", "n_unique_env_vars",
    "has_password_var", "has_apikey_var", "has_token_var", "has_oauth_vars",
    "n_capabilities", "n_lines", "has_version", "has_author",
    "mentions_2fa", "mentions_imessage", "sensitivity_score", "model_id",
]
X = sub[NUMERIC].fillna(-1)
y = (1 - sub["accept"]).astype(int)

tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=8, class_weight="balanced", random_state=0)
tree.fit(X, y)
perm = permutation_importance(tree, X, y, n_repeats=30, random_state=0, scoring="balanced_accuracy")
imp = pd.Series(perm.importances_mean, index=NUMERIC).sort_values()

colors_fi = ["#888"] * len(imp)
top3_idx = imp.tail(3).index
for i, name in enumerate(imp.index):
    if name in top3_idx:
        colors_fi[i] = "#C44E52"

ax.barh(range(len(imp)), imp.values, color=colors_fi, edgecolor="white")
ax.set_yticks(range(len(imp)))
ax.set_yticklabels(imp.index)
ax.set_xlabel("Permutation importance (predicting REFUSE)")
ax.set_title("Track B — feature importance (task-driven condition, n=255)")
ax.axvline(0, color="black", lw=0.8)
fig.tight_layout()
fig.savefig(FIGS / "fig5_feature_importance.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 6 — Skill ranking (top/bottom)
# ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True)
top = profile.sort_values("ASR_overall", ascending=False).head(15)
bot = profile.sort_values("ASR_overall").head(15)

for ax, data, title, color in [
    (axes[0], top.iloc[::-1], "TOP-15 highest ASR (always accepted)", "#55A868"),
    (axes[1], bot, "BOTTOM-15 lowest ASR (most resistant)", "#C44E52"),
]:
    bars = ax.barh(range(len(data)), data["ASR_overall"].values,
                   color=[sens_color[s] for s in data["sensitivity"]],
                   edgecolor="white")
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([f"{n} ({c})" for n, c in zip(data["skill_name"], data["category"])], fontsize=9)
    ax.set_xlabel("ASR")
    ax.set_title(title)
    ax.set_xlim(0, 1.1)
    for b, v in zip(bars, data["ASR_overall"].values):
        ax.text(v + 0.01, b.get_y() + b.get_height()/2, f"{v:.2f}", va="center", fontsize=8)

# shared legend
legend_handles = [
    Patch(facecolor=sens_color["high"], label="prior=HIGH"),
    Patch(facecolor=sens_color["medium"], label="prior=MEDIUM"),
    Patch(facecolor=sens_color["low"], label="prior=LOW"),
    Patch(facecolor=sens_color["unknown"], label="unknown"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=4, frameon=False)
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig(FIGS / "fig6_skill_ranking.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 7 — 2x2 summary panel
# ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(13, 9))

# (a) condition x model heatmap (mini)
ax = axes[0, 0]
im = ax.imshow(heat.values, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(MODELS, fontsize=9)
ax.set_yticks(range(3)); ax.set_yticklabels(CONDS, fontsize=9)
for i in range(3):
    for j in range(3):
        v = heat.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v > 0.6 else "black", fontsize=10, fontweight="bold")
ax.set_title("(a) Accept rate: condition × model")

# (b) ASR distribution
ax = axes[0, 1]
ax.hist(asr, bins=bins, color="#4C72B0", edgecolor="white", alpha=0.85)
ax.axvline(asr.mean(), color="#C44E52", linestyle="--", lw=2, label=f"mean={asr.mean():.3f}")
ax.axvline(0.7, color="black", linestyle=":", lw=1.5, alpha=0.5)
ax.set_xlabel("Per-skill ASR")
ax.set_ylabel("# skills")
ax.set_title("(b) Per-skill ASR distribution (n=85)")
ax.legend(fontsize=9)

# (c) Macro ATE
ax = axes[1, 0]
for i, m in enumerate(MODELS):
    vals = ate[ate["model"] == m].set_index("condition").loc[["trust-badge", "task-driven"], "ate"]
    ax.bar(np.arange(2) + (i - 1) * width, vals.values, width, color=COLOR_M[m], label=m, edgecolor="white")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(np.arange(2)); ax.set_xticklabels(["+trust-badge", "+task-driven"], fontsize=10)
ax.set_ylabel("Δ accept rate")
ax.set_title("(c) Macro ATE per model")
ax.legend(fontsize=9, loc="lower right")
ax.grid(axis="y", alpha=0.3)

# (d) category ASR (top/bottom 6 each)
ax = axes[1, 1]
ranked = cat_asr.copy()
combined = pd.concat([ranked.head(6), ranked.tail(6)])
combined = combined.iloc[::-1]
ax.barh(range(len(combined)), combined["asr"].values,
        color=[sens_color[s] for s in combined["sens"]], edgecolor="white")
ax.set_yticks(range(len(combined)))
ax.set_yticklabels(combined.index, fontsize=9)
ax.set_xlabel("Mean ASR")
ax.set_title("(d) Top vs bottom categories by ASR")
ax.axvline(profile["ASR_overall"].mean(), color="black", linestyle="--", lw=1, alpha=0.5)
ax.set_xlim(0, 1.1)

fig.suptitle("XAI Prototype v0 — Summary  (canifi 85 skills × 3 models × 3 conditions = 765 decisions)",
             fontsize=13, fontweight="bold", y=1.00)
fig.tight_layout()
fig.savefig(FIGS / "fig7_summary.png")
plt.close(fig)

print("Wrote 7 figures to:", FIGS)
for f in sorted(FIGS.iterdir()):
    print(f"  {f.name}  ({f.stat().st_size//1024} KB)")
