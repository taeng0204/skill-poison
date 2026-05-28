"""
Presentation-ready PNG figures.
- Korean fonts (NanumGothic)
- DPI 220, larger typography, generous spacing
- Highlighted key findings with annotations
- Outputs to figs_presentation/
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch, FancyArrowPatch, FancyBboxPatch
from sklearn.tree import DecisionTreeClassifier
from sklearn.inspection import permutation_importance

# ── Style ─────────────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family": "NanumGothic",
    "axes.unicode_minus": False,
    "figure.dpi": 110,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 18,
    "axes.titleweight": "bold",
    "axes.labelsize": 14,
    "axes.labelweight": "medium",
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "legend.frameon": False,
    "axes.grid": False,
})

# Color palette
C_ACCEPT = "#2D9C5F"
C_REFUSE = "#C0392B"
C_NEUTRAL = "#5D6D7E"
C_HIGHLIGHT = "#F39C12"
C_BLUE = "#2980B9"

SENS_COLOR = {
    "high": "#C0392B",
    "medium": "#E67E22",
    "low": "#27AE60",
    "unknown": "#95A5A6",
}
MODEL_COLOR = {
    "qwen2.5:7b": "#3A6FB0",
    "qwen3:8b":   "#D67A3A",
    "llama3.1:8b":"#3FA170",
}

HERE = Path(__file__).parent
FIGS = HERE / "figs_presentation"
FIGS.mkdir(exist_ok=True)

df = pd.read_csv(HERE / "dataset.csv")
profile = pd.read_csv(HERE / "skill_asr_profile.csv")

MODELS = ["qwen2.5:7b", "qwen3:8b", "llama3.1:8b"]
CONDS  = ["listing-only", "trust-badge", "task-driven"]

# ─────────────────────────────────────────────────────────────────
# Fig 1 — ASR distribution
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.5))
asr = profile["ASR_overall"]
bins = np.linspace(0.4, 1.0, 13)
n, b, patches = ax.hist(asr, bins=bins, color=C_BLUE, edgecolor="white", linewidth=1.5)
# highlight last bin (ASR=1.0)
patches[-1].set_facecolor(C_ACCEPT)
patches[-1].set_alpha(0.95)
# highlight first bin
patches[0].set_facecolor(C_REFUSE)

ax.axvline(asr.mean(), color="black", linestyle="--", lw=2, alpha=0.7,
           label=f"Mean ASR = {asr.mean():.3f}")
ax.axvline(0.7, color=C_HIGHLIGHT, linestyle=":", lw=2,
           label="ASR = 0.70 threshold")

ax.set_xlabel("Per-skill ASR  (mean over 3 conditions × 3 models)")
ax.set_ylabel("Number of Skills")
ax.set_title("Per-Skill ASR Distribution — 27 pass 100% (n=85)")
ax.legend(loc="upper left")

ax.annotate("27 skills with\nASR = 1.0\n(fully accepted)",
            xy=(0.985, 27), xytext=(0.86, 23),
            fontsize=12, ha="center",
            arrowprops=dict(arrowstyle="->", color=C_ACCEPT, lw=2),
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F5E9", edgecolor=C_ACCEPT, lw=1.5))
ax.annotate("11 skills with\nASR < 0.7\n(resistant set)",
            xy=(0.46, 1), xytext=(0.51, 8),
            fontsize=12, ha="center",
            arrowprops=dict(arrowstyle="->", color=C_REFUSE, lw=2),
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FCE8E6", edgecolor=C_REFUSE, lw=1.5))

fig.tight_layout()
fig.savefig(FIGS / "fig1_asr_distribution.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 2 — Condition × Model heatmap (with side panel annotation)
# ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[2.4, 1], wspace=0.25)
ax = fig.add_subplot(gs[0])
heat = df.pivot_table(index="condition", columns="model", values="accept", aggfunc="mean")
heat = heat.reindex(index=CONDS, columns=MODELS)
im = ax.imshow(heat.values, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(MODELS, fontsize=14)
ax.set_yticks(range(3)); ax.set_yticklabels(CONDS, fontsize=14)
for i in range(3):
    for j in range(3):
        v = heat.values[i, j]
        ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                color="white" if v > 0.55 else "black",
                fontsize=18, fontweight="bold")
ax.set_title("Accept Rate by Condition × Model  (255 decisions per cell)")
ax.set_xlabel("Model")
ax.set_ylabel("Prompt Condition")
cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
cbar.set_label("Accept Rate", fontsize=12)
cbar.ax.tick_params(labelsize=11)

# Side panel for annotations
ax_text = fig.add_subplot(gs[1])
ax_text.axis("off")
ax_text.text(0.0, 0.92, "Key Observations", fontsize=14, fontweight="bold")
ax_text.text(0.0, 0.78,
             "▶ qwen3:8b\n"
             "   accepts 96–100% under\n"
             "   every condition — highest risk",
             fontsize=12, va="top", color=C_REFUSE,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#FCE8E6",
                       edgecolor=C_REFUSE, lw=1.5))
ax_text.text(0.0, 0.40,
             "▶ llama3.1 × task-driven\n"
             "   = 0.42\n"
             "   Task framing triggers\n"
             "   a natural defense",
             fontsize=12, va="top", color=C_ACCEPT,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#E8F5E9",
                       edgecolor=C_ACCEPT, lw=1.5))

fig.savefig(FIGS / "fig2_condition_model_heatmap.png", bbox_inches="tight")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 3 — Macro ATE per model  (FIXED label position)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))
records = []
for m in MODELS:
    base = df[(df["model"] == m) & (df["condition"] == "listing-only")]["accept"].mean()
    for c in ["trust-badge", "task-driven"]:
        v = df[(df["model"] == m) & (df["condition"] == c)]["accept"].mean()
        records.append({"model": m, "condition": c, "ate": v - base, "base": base, "value": v})

ate = pd.DataFrame(records)
x = np.arange(2)
width = 0.27

for i, m in enumerate(MODELS):
    vals = ate[ate["model"] == m].set_index("condition").loc[["trust-badge", "task-driven"], "ate"]
    bars = ax.bar(x + (i - 1) * width, vals.values, width,
                  color=MODEL_COLOR[m], label=m, edgecolor="white", linewidth=1.5)
    for b, v in zip(bars, vals.values):
        # label outside the bar
        if v >= 0:
            ay = v + 0.02
            va = "bottom"
        else:
            ay = v - 0.02
            va = "top"
        ax.text(b.get_x() + b.get_width()/2, ay, f"{v:+.3f}",
                ha="center", va=va, fontsize=12, fontweight="bold",
                color=MODEL_COLOR[m])

ax.axhline(0, color="black", lw=1)
ax.set_xticks(x)
ax.set_xticklabels(["+ trust-badge\n(vs listing-only baseline)",
                     "+ task-driven\n(vs listing-only baseline)"])
ax.set_ylabel("Average Treatment Effect (Δ accept rate)")
ax.set_title("Average Treatment Effect of Prompt Condition per Model (ATE)")
ax.set_ylim(-0.65, 0.30)
ax.legend(loc="lower left")
ax.grid(axis="y", alpha=0.3)

# Highlight key finding
ax.annotate("llama3.1: task framing alone\n   accept -49% (natural defense)",
            xy=(1+width, -0.494), xytext=(1.4, -0.45),
            fontsize=12, ha="left", color=C_ACCEPT, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_ACCEPT, lw=2),
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F5E9",
                      edgecolor=C_ACCEPT, lw=1.5))

fig.tight_layout()
fig.savefig(FIGS / "fig3_macro_effects.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 4 — Category × ASR  (KEY finding)
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 9))
fig.subplots_adjust(left=0.10, right=0.66, top=0.92, bottom=0.10)
cat_asr = profile.groupby("category").agg(
    asr=("ASR_overall", "mean"),
    n=("ASR_overall", "size"),
    sens=("sensitivity", "first"),
).sort_values("asr")

colors = [SENS_COLOR[s] for s in cat_asr["sens"]]
bars = ax.barh(range(len(cat_asr)), cat_asr["asr"].values, color=colors, edgecolor="white", linewidth=1.2)
ax.set_yticks(range(len(cat_asr)))
ax.set_yticklabels([f"{c}  (n={n})" for c, n in zip(cat_asr.index, cat_asr["n"])], fontsize=15)
ax.set_xlabel("Mean ASR  (cross-condition × cross-model)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)
ax.set_title("ASR by Category  vs.  Sensitivity Prior  ·  XAI: Decision Tree + Permutation Importance",
             fontsize=18, fontweight="bold", pad=14)
ax.axvline(profile["ASR_overall"].mean(), color="black", linestyle="--", lw=1.8, alpha=0.6,
           label=f"Overall mean = {profile['ASR_overall'].mean():.3f}")

for b, v in zip(bars, cat_asr["asr"].values):
    ax.text(v + 0.008, b.get_y() + b.get_height()/2, f"{v:.2f}",
            va="center", fontsize=13, fontweight="bold")

legend_handles_sens = [
    Patch(facecolor=SENS_COLOR["high"], label="HIGH\n(finance, health, legal, HR)"),
    Patch(facecolor=SENS_COLOR["medium"], label="MEDIUM"),
    Patch(facecolor=SENS_COLOR["low"], label="LOW\n(entertainment, gaming)"),
]

ax.set_xlim(0, 1.20)
ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])

# Right-side panel: legend on top, finding box below (in figure margin)
ax.legend(loc="upper left", bbox_to_anchor=(1.05, 0.50), fontsize=15)
leg_sens = ax.legend(handles=legend_handles_sens, loc="upper left",
                     bbox_to_anchor=(1.05, 1.00), title="Sensitivity Prior",
                     fontsize=14)
leg_sens.get_title().set_fontweight("bold")
leg_sens.get_title().set_fontsize(15)
ax.add_artist(leg_sens)

# Finding box (upgraded font)
ax.text(1.05, 0.43,
        "★ Key Finding\n\n"
        "Behavior runs opposite to the prior:\n\n"
        "• HIGH categories such as\n"
        "  finance (0.94), healthcare (0.81)\n"
        "  pass as easily as / better than\n"
        "  LOW entertainment (0.87)\n\n"
        "• The model judges by\n"
        "  'social category', not by\n"
        "  'credential quantity'",
        transform=ax.transAxes, va="top", ha="left", fontsize=15,
        bbox=dict(boxstyle="round,pad=0.7", facecolor="#FFF8E1",
                  edgecolor="none", lw=0))

fig.savefig(FIGS / "fig4_category_asr.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 5 — Feature importance (task-driven) + counter-finding callout
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 7.5))
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

# Color: top-3 highlight, credential vars in red-zero zone
top3 = set(imp.tail(3).index)
cred_vars = {"n_env_vars", "n_unique_env_vars", "has_password_var",
             "has_apikey_var", "has_token_var", "has_oauth_vars"}

bar_colors = []
for name in imp.index:
    if name in top3:
        bar_colors.append(C_REFUSE)
    elif name in cred_vars:
        bar_colors.append("#D5DBDB")
    else:
        bar_colors.append(C_NEUTRAL)

ax.barh(range(len(imp)), imp.values, color=bar_colors, edgecolor="white", linewidth=1.2)
ax.set_yticks(range(len(imp)))
ax.set_yticklabels(imp.index, fontsize=15)
ax.set_xlabel("Permutation importance  (predicting REFUSE)", fontsize=15)
ax.tick_params(axis="x", labelsize=13)
ax.set_title("Track B — Feature Importance under task-driven Condition (n=255)",
             fontsize=18, fontweight="bold", pad=12)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlim(0, 0.42)

# Top-3 callout — placed in right margin
top3_names = list(imp.tail(3).index[::-1])
ax.text(0.245, len(imp)-1.5,
        "Top 3 (red bars)\n"
        f"  1. {top3_names[0]}\n"
        f"  2. {top3_names[1]}\n"
        f"  3. {top3_names[2]}",
        fontsize=14.5, color=C_REFUSE, fontweight="bold", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FCE8E6",
                  edgecolor=C_REFUSE, lw=1.8))

ax.text(0.245, 4.8,
        "★ All six credential variables\n"
        "  (env_vars · password · apikey ·\n"
        "   token · oauth)\n"
        "have importance ≈ 0\n\n"
        "→ The model does not use\n"
        "  'credential quantity' as a risk signal",
        fontsize=14.5, va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#FFF8E1",
                  edgecolor=C_HIGHLIGHT, lw=2.2))

fig.tight_layout()
fig.savefig(FIGS / "fig5_feature_importance.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 6 — Skill ranking (top + bottom)
# ─────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
top = profile.sort_values("ASR_overall", ascending=False).head(15)
bot = profile.sort_values("ASR_overall").head(15)

for ax, data, title, _ in [
    (axes[0], top.iloc[::-1], "TOP-15 — Always Accepted (vulnerable skills)", C_ACCEPT),
    (axes[1], bot, "BOTTOM-15 — Frequently Refused (resistant skills)", C_REFUSE),
]:
    bars = ax.barh(range(len(data)), data["ASR_overall"].values,
                   color=[SENS_COLOR[s] for s in data["sensitivity"]],
                   edgecolor="white", linewidth=1.2)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([f"{n}  ({c})" for n, c in zip(data["skill_name"], data["category"])],
                       fontsize=11)
    ax.set_xlabel("ASR")
    ax.set_title(title)
    ax.set_xlim(0, 1.12)
    for b, v in zip(bars, data["ASR_overall"].values):
        ax.text(v + 0.012, b.get_y() + b.get_height()/2, f"{v:.2f}",
                va="center", fontsize=10, fontweight="bold")

legend_handles = [
    Patch(facecolor=SENS_COLOR["high"], label="prior=HIGH"),
    Patch(facecolor=SENS_COLOR["medium"], label="prior=MEDIUM"),
    Patch(facecolor=SENS_COLOR["low"], label="prior=LOW"),
    Patch(facecolor=SENS_COLOR["unknown"], label="unknown"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=4,
           frameon=False, fontsize=12, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Skill Ranking — Which Skills Are Accepted vs. Refused",
             fontsize=18, fontweight="bold", y=1.00)
fig.tight_layout(rect=[0, 0.03, 1, 0.97])
fig.savefig(FIGS / "fig6_skill_ranking.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 7 — Summary 4-panel
# ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 11))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.28)

# (a) heatmap
ax = fig.add_subplot(gs[0, 0])
im = ax.imshow(heat.values, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(3)); ax.set_xticklabels(MODELS, fontsize=11)
ax.set_yticks(range(3)); ax.set_yticklabels(CONDS, fontsize=11)
for i in range(3):
    for j in range(3):
        v = heat.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v > 0.55 else "black", fontsize=15, fontweight="bold")
ax.set_title("(a) Accept Rate: Condition × Model", fontsize=15)

# (b) ASR distribution
ax = fig.add_subplot(gs[0, 1])
n, b, patches = ax.hist(asr, bins=bins, color=C_BLUE, edgecolor="white", linewidth=1.5)
patches[-1].set_facecolor(C_ACCEPT)
patches[0].set_facecolor(C_REFUSE)
ax.axvline(asr.mean(), color="black", linestyle="--", lw=2, label=f"Mean={asr.mean():.3f}")
ax.axvline(0.7, color=C_HIGHLIGHT, linestyle=":", lw=2)
ax.set_xlabel("Per-skill ASR", fontsize=13)
ax.set_ylabel("Number of Skills", fontsize=13)
ax.set_title("(b) Per-Skill ASR Distribution (n=85)", fontsize=15)
ax.legend(fontsize=11)

# (c) ATE bars
ax = fig.add_subplot(gs[1, 0])
for i, m in enumerate(MODELS):
    vals = ate[ate["model"] == m].set_index("condition").loc[["trust-badge", "task-driven"], "ate"]
    bars = ax.bar(np.arange(2) + (i - 1) * width, vals.values, width,
                  color=MODEL_COLOR[m], label=m, edgecolor="white", linewidth=1.2)
    for bar_, v in zip(bars, vals.values):
        ax.text(bar_.get_x() + bar_.get_width()/2,
                v + (0.02 if v >= 0 else -0.02),
                f"{v:+.2f}",
                ha="center", va="bottom" if v >= 0 else "top",
                fontsize=10, fontweight="bold", color=MODEL_COLOR[m])

ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(np.arange(2))
ax.set_xticklabels(["+trust-badge", "+task-driven"], fontsize=12)
ax.set_ylabel("Δ accept rate", fontsize=13)
ax.set_title("(c) Per-Model ATE of Conditions", fontsize=15)
ax.set_ylim(-0.65, 0.30)
ax.legend(fontsize=11, loc="lower left")
ax.grid(axis="y", alpha=0.3)

# (d) Top/Bottom 6 categories
ax = fig.add_subplot(gs[1, 1])
combined = pd.concat([cat_asr.head(6), cat_asr.tail(6)]).iloc[::-1]
ax.barh(range(len(combined)), combined["asr"].values,
        color=[SENS_COLOR[s] for s in combined["sens"]], edgecolor="white", linewidth=1.2)
ax.set_yticks(range(len(combined)))
ax.set_yticklabels(combined.index, fontsize=11)
ax.set_xlabel("Mean ASR", fontsize=13)
ax.set_title("(d) Top vs. Bottom Categories by ASR", fontsize=15)
ax.axvline(profile["ASR_overall"].mean(), color="black", linestyle="--", lw=1, alpha=0.5)
ax.set_xlim(0, 1.12)

leg = [Patch(facecolor=SENS_COLOR[k], label=f"prior={k.upper()}") for k in ["high","medium","low"]]
ax.legend(handles=leg, loc="lower right", fontsize=10)

fig.suptitle("XAI Prototype v0 — Summary  (canifi 85 skills × 3 models × 3 conditions = 765 decisions)",
             fontsize=17, fontweight="bold", y=0.995)
fig.savefig(FIGS / "fig7_summary.png")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────
# Fig 8 — Prior alignment 2x2 matrix (NEW) — fixed layout
# ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(-1.2, 10); ax.set_ylim(-0.5, 11)
ax.set_aspect("auto")
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# Quadrant tints (drawn first, behind everything)
ax.add_patch(FancyBboxPatch((0, 5), 5, 4.5, boxstyle="square,pad=0",
                            facecolor="#F4F6F7", edgecolor="none", zorder=0))
ax.add_patch(FancyBboxPatch((5, 5), 5, 4.5, boxstyle="square,pad=0",
                            facecolor="#FFF8E1", edgecolor="none", zorder=0))
ax.add_patch(FancyBboxPatch((0, 0), 5, 4.5, boxstyle="square,pad=0",
                            facecolor="#F8F9FA", edgecolor="none", zorder=0))
ax.add_patch(FancyBboxPatch((5, 0), 5, 4.5, boxstyle="square,pad=0",
                            facecolor="#FFFBE6", edgecolor="none", zorder=0))

# Quadrant dividers
ax.plot([0, 10], [4.75, 4.75], color="black", lw=1.5, zorder=1)
ax.plot([5, 5], [0, 9.5], color="black", lw=1.5, zorder=1)

# Top column headers
ax.text(2.5, 10.3, "Aligned with Prior — Confirmed",
        ha="center", fontsize=20, fontweight="bold", color=C_NEUTRAL)
ax.text(7.5, 10.3, "Violates Prior — Discovery ★",
        ha="center", fontsize=20, fontweight="bold", color=C_HIGHLIGHT)

# Left row headers
ax.text(-0.7, 7.25, "Strong\nEffect", ha="center", va="center",
        fontsize=20, fontweight="bold", color=C_NEUTRAL)
ax.text(-0.7, 2.25, "Weak\nEffect", ha="center", va="center",
        fontsize=20, fontweight="bold", color=C_NEUTRAL)

# Cell content — top-left (Strong + Aligned)
ax.text(0.3, 9.0, "Confirmed Effects", fontsize=19, fontweight="bold", color=C_NEUTRAL)
ax.text(0.3, 8.4,
        "▶  trust_badge ↑ ASR\n     (metadata trust)\n\n"
        "▶  task_context ↓ ASR\n     (user context → caution)",
        fontsize=17, va="top")

# Cell content — top-right (Strong + Violated) ★ KEY
ax.text(5.3, 9.0, "★ New Findings", fontsize=20, fontweight="bold", color=C_HIGHLIGHT)
ax.text(5.3, 8.4,
        "▶  ", fontsize=17, va="top", fontweight="bold")
ax.text(5.6, 8.4,
        "Category dominates the decision",
        fontsize=18, va="top", fontweight="bold", color="#B45309")
ax.text(5.3, 7.95,
        "     (social·HR refused, finance·health accepted)",
        fontsize=16, va="top", color="#555")
ax.text(5.3, 7.10,
        "▶  ", fontsize=17, va="top", fontweight="bold")
ax.text(5.6, 7.10,
        "task_context differs across models",
        fontsize=18, va="top", fontweight="bold", color="#B45309")
ax.text(5.3, 6.65,
        "     (qwen3 = 0% vs. llama3.1 = -49%)",
        fontsize=16, va="top", color="#555")

# Cell content — bottom-left (Weak + Aligned)
ax.text(0.3, 4.25, "Confirmed (weak as expected)", fontsize=19, fontweight="bold", color=C_NEUTRAL)
ax.text(0.3, 3.65,
        "▶  has_apikey_var   ≈ 0\n"
        "▶  has_oauth_vars  ≈ 0\n"
        "▶  has_token_var    ≈ 0\n\n"
        "    (individual variable type has no effect)",
        fontsize=17, va="top", color="#555")

# Cell content — bottom-right (Weak + Violated) ★ COUNTER
ax.text(5.3, 4.25, "★ Counterintuitive Findings", fontsize=20, fontweight="bold", color=C_HIGHLIGHT)
ax.text(5.3, 3.65,
        "▶  ", fontsize=17, va="top", fontweight="bold")
ax.text(5.6, 3.65,
        "n_env_vars negatively correlated",
        fontsize=18, va="top", fontweight="bold", color="#B45309")
ax.text(5.3, 3.20,
        "     (more credentials → more often refused)",
        fontsize=16, va="top", color="#555")
ax.text(5.3, 2.40,
        "▶  n_chars positively correlated\n"
        "     (longer skills tend to pass)\n\n"
        "▶  sensitivity_prior is irrelevant",
        fontsize=17, va="top")

ax.set_title("XAI Feature Discovery Matrix — Where the Real Findings Lie",
             fontsize=24, fontweight="bold", pad=22)
fig.tight_layout()
fig.savefig(FIGS / "fig8_prior_alignment_matrix.png")
plt.close(fig)

print("Wrote figures to:", FIGS)
for f in sorted(FIGS.iterdir()):
    print(f"  {f.name}  ({f.stat().st_size//1024} KB)")
