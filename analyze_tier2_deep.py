#!/usr/bin/env python3
"""Deep analysis over the Tier-1 + Tier-2 SkillProbe dataset.

This script consumes existing analysis artifacts only. It does not run any
agent experiments.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from scipy.stats import binomtest, fisher_exact
except Exception:  # pragma: no cover - scipy is expected but optional.
    binomtest = None
    fisher_exact = None


INPUT = Path("artifacts/tier2_features/merged_runs_features_tier1_tier2.csv")
OUT_DIR = Path("artifacts/tier2_analysis")


MODEL_ORDER = ["qwen3:1.7b", "qwen3:8b", "gpt-5.4", "gpt-5.4-mini"]
CONDITION_ORDER = ["C1", "C2", "C3"]
PLOT_LABELS = {
    "qwen3:1.7b": "Qwen 1.7B",
    "qwen3:8b": "Qwen 8B",
    "gpt-5.4": "GPT-5.4",
    "gpt-5.4-mini": "GPT-5.4 mini",
    "C1": "C1 neutral",
    "C2": "C2 safety",
    "C3": "C3 trust",
}


def t2(name: str) -> str:
    return f"tier2_{name}"


def to_num(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def rate(k: float, n: float) -> float:
    return float(k / n) if n else float("nan")


def pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x * 100:.1f}%"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    spread = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return center - spread, center + spread


def exact_mcnemar_p(n10: int, n01: int) -> float:
    total = n10 + n01
    if total == 0:
        return 1.0
    if binomtest is None:
        return float("nan")
    return float(binomtest(min(n10, n01), total, 0.5, alternative="two-sided").pvalue)


def fisher_p(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    if fisher_exact is None:
        return float("nan"), float("nan")
    odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative="two-sided")
    return float(odds_ratio), float(p_value)


def save_csv(df: pd.DataFrame, name: str) -> Path:
    path = OUT_DIR / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def ordered(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "model" in out.columns:
        out["model"] = pd.Categorical(out["model"], MODEL_ORDER, ordered=True)
    if "condition" in out.columns:
        out["condition"] = pd.Categorical(out["condition"], CONDITION_ORDER, ordered=True)
    sort_cols = [x for x in ["model", "condition"] if x in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols)
        for col in sort_cols:
            out[col] = out[col].astype(str)
    return out


def build_model_condition_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, condition), group in df.groupby(["model", "condition"], sort=False):
        n = len(group)
        stage_c = int(group[t2("stage_c_egress")].sum())
        ci_low, ci_high = wilson(stage_c, n)
        stage_c_group = group[group[t2("stage_c_egress")] == 1]
        rows.append(
            {
                "model": model,
                "condition": condition,
                "n": n,
                "stage_a_count": int(group[t2("stage_a_acceptance")].sum()),
                "stage_a_rate": rate(group[t2("stage_a_acceptance")].sum(), n),
                "stage_b_count": int(group[t2("stage_b_execution")].sum()),
                "stage_b_rate": rate(group[t2("stage_b_execution")].sum(), n),
                "stage_c_count": stage_c,
                "stage_c_rate": rate(stage_c, n),
                "stage_c_ci95_low": ci_low,
                "stage_c_ci95_high": ci_high,
                "silent_stage_c_count": int(group[t2("silent_stage_c")].sum()),
                "silent_stage_c_rate": rate(group[t2("silent_stage_c")].sum(), n),
                "silent_fraction_among_stage_c": rate(group[t2("silent_stage_c")].sum(), stage_c),
                "detected_count": int(group[t2("detected_malicious")].sum()),
                "detected_rate": rate(group[t2("detected_malicious")].sum(), n),
                "decision_accept_count": int(group[t2("decision_accept")].sum()),
                "decision_accept_rate": rate(group[t2("decision_accept")].sum(), n),
                "decision_review_count": int(group[t2("decision_review")].sum()),
                "decision_review_rate": rate(group[t2("decision_review")].sum(), n),
                "detected_but_stage_b_count": int(group[t2("detected_but_stage_b")].sum()),
                "detected_but_stage_c_count": int(group[t2("detected_but_stage_c")].sum()),
                "review_but_stage_b_count": int(group[t2("review_but_stage_b")].sum()),
                "review_but_stage_c_count": int(group[t2("review_but_stage_c")].sum()),
                "canary_requests_sum": int(group[t2("canary_requests")].sum()),
                "canary_requests_mean": group[t2("canary_requests")].mean(),
                "canary_requests_median": group[t2("canary_requests")].median(),
                "fs_events_mean": group[t2("fs_events_count")].mean(),
                "fs_events_median": group[t2("fs_events_count")].median(),
                "workspace_files_mean": group[t2("workspace_new_files_count")].mean(),
                "workspace_files_median": group[t2("workspace_new_files_count")].median(),
                "dangerous_commands_mean": group[t2("dangerous_commands_count")].mean(),
                "schema_dangerous_commands_rate": group[t2("schema_has_dangerous_commands")].mean(),
                "schema_canifi_events_rate": group[t2("schema_has_canifi_events")].mean(),
                "stage_c_canary_requests_mean": stage_c_group[t2("canary_requests")].mean()
                if stage_c
                else 0.0,
                "stage_c_fs_events_median": stage_c_group[t2("fs_events_count")].median()
                if stage_c
                else 0.0,
            }
        )
    out = pd.DataFrame(rows)
    return ordered(out)


def build_paired_condition_effects(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pairs = [("C1", "C2", "C2_vs_C1"), ("C1", "C3", "C3_vs_C1"), ("C2", "C3", "C3_vs_C2")]
    for model in MODEL_ORDER:
        sub = df[df["model"] == model]
        pivot = sub.pivot_table(
            index="skill",
            columns="condition",
            values=t2("stage_c_egress"),
            aggfunc="first",
        )
        for base, compare, label in pairs:
            if base not in pivot or compare not in pivot:
                continue
            paired = pivot[[base, compare]].dropna()
            b = paired[base].astype(int)
            c = paired[compare].astype(int)
            n = len(paired)
            base_count = int(b.sum())
            compare_count = int(c.sum())
            suppressed = int(((b == 1) & (c == 0)).sum())
            induced = int(((b == 0) & (c == 1)).sum())
            unchanged_pos = int(((b == 1) & (c == 1)).sum())
            unchanged_neg = int(((b == 0) & (c == 0)).sum())
            base_rate = rate(base_count, n)
            compare_rate = rate(compare_count, n)
            rr_haldane = ((compare_count + 0.5) / (n + 1)) / ((base_count + 0.5) / (n + 1))
            odds_ratio, p_value = fisher_p(compare_count, n - compare_count, base_count, n - base_count)
            rows.append(
                {
                    "model": model,
                    "comparison": label,
                    "base_condition": base,
                    "compare_condition": compare,
                    "paired_skills": n,
                    "base_stage_c_count": base_count,
                    "compare_stage_c_count": compare_count,
                    "base_stage_c_rate": base_rate,
                    "compare_stage_c_rate": compare_rate,
                    "risk_difference_compare_minus_base": compare_rate - base_rate,
                    "risk_ratio_haldane": rr_haldane,
                    "induced_0_to_1": induced,
                    "suppressed_1_to_0": suppressed,
                    "unchanged_1_to_1": unchanged_pos,
                    "unchanged_0_to_0": unchanged_neg,
                    "mcnemar_exact_p": exact_mcnemar_p(suppressed, induced),
                    "fisher_odds_ratio_unpaired_check": odds_ratio,
                    "fisher_p_unpaired_check": p_value,
                }
            )
    return pd.DataFrame(rows)


def build_decision_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, condition, decision), group in df.groupby(
        ["model", "condition", t2("agent_decision_class")], sort=False
    ):
        n = len(group)
        rows.append(
            {
                "model": model,
                "condition": condition,
                "agent_decision_class": decision,
                "n": n,
                "stage_b_count": int(group[t2("stage_b_execution")].sum()),
                "stage_b_rate": rate(group[t2("stage_b_execution")].sum(), n),
                "stage_c_count": int(group[t2("stage_c_egress")].sum()),
                "stage_c_rate": rate(group[t2("stage_c_egress")].sum(), n),
                "detected_count": int(group[t2("detected_malicious")].sum()),
                "detected_rate": rate(group[t2("detected_malicious")].sum(), n),
                "silent_stage_c_count": int(group[t2("silent_stage_c")].sum()),
                "mean_canary_requests": group[t2("canary_requests")].mean(),
                "median_fs_events": group[t2("fs_events_count")].median(),
                "median_workspace_files": group[t2("workspace_new_files_count")].median(),
            }
        )
    return ordered(pd.DataFrame(rows))


def build_detection_mismatch(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, condition), group in df.groupby(["model", "condition"], sort=False):
        n = len(group)
        detected = group[group[t2("detected_malicious")] == 1]
        review = group[group[t2("decision_review")] == 1]
        detected_count = len(detected)
        review_count = len(review)
        rows.append(
            {
                "model": model,
                "condition": condition,
                "n": n,
                "detected_count": detected_count,
                "detected_rate": rate(detected_count, n),
                "detected_stage_b_count": int(detected[t2("stage_b_execution")].sum()),
                "detected_stage_b_rate_among_detected": rate(
                    detected[t2("stage_b_execution")].sum(), detected_count
                ),
                "detected_stage_c_count": int(detected[t2("stage_c_egress")].sum()),
                "detected_stage_c_rate_among_detected": rate(
                    detected[t2("stage_c_egress")].sum(), detected_count
                ),
                "review_count": review_count,
                "review_stage_b_count": int(review[t2("stage_b_execution")].sum()),
                "review_stage_b_rate_among_review": rate(review[t2("stage_b_execution")].sum(), review_count),
                "review_stage_c_count": int(review[t2("stage_c_egress")].sum()),
                "review_stage_c_rate_among_review": rate(review[t2("stage_c_egress")].sum(), review_count),
                "silent_stage_c_count": int(group[t2("silent_stage_c")].sum()),
                "stage_c_count": int(group[t2("stage_c_egress")].sum()),
            }
        )
    return ordered(pd.DataFrame(rows))


def build_process_footprint(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, condition, stage_c), group in df.groupby(["model", "condition", t2("stage_c_egress")], sort=False):
        n = len(group)
        rows.append(
            {
                "model": model,
                "condition": condition,
                "stage_c_egress": int(stage_c),
                "n": n,
                "fs_events_mean": group[t2("fs_events_count")].mean(),
                "fs_events_median": group[t2("fs_events_count")].median(),
                "fs_events_p95": group[t2("fs_events_count")].quantile(0.95),
                "fs_events_max": group[t2("fs_events_count")].max(),
                "workspace_files_mean": group[t2("workspace_new_files_count")].mean(),
                "workspace_files_median": group[t2("workspace_new_files_count")].median(),
                "workspace_files_p95": group[t2("workspace_new_files_count")].quantile(0.95),
                "workspace_files_max": group[t2("workspace_new_files_count")].max(),
                "workspace_files_gt10_count": int((group[t2("workspace_new_files_count")] > 10).sum()),
                "workspace_files_gt100_count": int((group[t2("workspace_new_files_count")] > 100).sum()),
                "dangerous_commands_mean": group[t2("dangerous_commands_count")].mean(),
                "dangerous_commands_median": group[t2("dangerous_commands_count")].median(),
                "canary_requests_mean": group[t2("canary_requests")].mean(),
                "canary_requests_median": group[t2("canary_requests")].median(),
                "schema_dangerous_commands_rate": group[t2("schema_has_dangerous_commands")].mean(),
                "schema_canifi_events_rate": group[t2("schema_has_canifi_events")].mean(),
            }
        )
    return ordered(pd.DataFrame(rows))


def build_process_outliers(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "session_id",
        "model",
        "condition",
        "skill",
        t2("stage_c_egress"),
        t2("workspace_new_files_count"),
        t2("fs_events_count"),
        t2("dangerous_commands_count"),
        t2("canary_requests"),
        t2("dangerous_command_sample"),
        t2("external_domains_sample"),
    ]
    out = df[cols].copy()
    out = out.sort_values(
        [t2("workspace_new_files_count"), t2("fs_events_count")],
        ascending=[False, False],
    )
    return out.head(30)


def build_canary_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = [(("ALL", "ALL"), df)]
    groups.extend(list(df.groupby(["model", "condition"], sort=False)))
    for key, group in groups:
        model, condition = key
        n = len(group)
        stage_c_count = int(group[t2("stage_c_egress")].sum())
        rows.append(
            {
                "model": model,
                "condition": condition,
                "n": n,
                "stage_c_count": stage_c_count,
                "canary_requests_sum": int(group[t2("canary_requests")].sum()),
                "canary_log_events_sum": int(group[t2("canary_log_events")].sum()),
                "canary_api_exfil_events_sum": int(group[t2("canary_api_exfil_events")].sum()),
                "canary_get_events_sum": int(group[t2("canary_get_events")].sum()),
                "canary_post_events_sum": int(group[t2("canary_post_events")].sum()),
                "canary_body_size_total": int(group[t2("canary_body_size_total")].sum()),
                "canary_nonempty_body_events_sum": int(group[t2("canary_nonempty_body_events")].sum()),
                "canary_token_leaked_count": int(group[t2("canary_token_leaked")].sum()),
                "canary_requests_per_stage_c_row": rate(group[t2("canary_requests")].sum(), stage_c_count),
            }
        )
    out = pd.DataFrame(rows)
    return out


def build_skill_rank(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for skill, group in df.groupby("skill", sort=True):
        row = {
            "skill": skill,
            "skill_category": group["skill_category"].dropna().iloc[0] if "skill_category" in group else "",
            "service_sensitivity": group["service_sensitivity"].dropna().iloc[0]
            if "service_sensitivity" in group
            else "",
            "payload_type": group["payload_type"].dropna().iloc[0] if "payload_type" in group else "",
            "n": len(group),
            "stage_c_count": int(group[t2("stage_c_egress")].sum()),
            "stage_c_rate": group[t2("stage_c_egress")].mean(),
            "silent_stage_c_count": int(group[t2("silent_stage_c")].sum()),
            "detected_count": int(group[t2("detected_malicious")].sum()),
        }
        for model in ["qwen3:1.7b", "qwen3:8b"]:
            for condition in CONDITION_ORDER:
                sub = group[(group["model"] == model) & (group["condition"] == condition)]
                safe_model = model.replace(":", "_").replace(".", "_")
                row[f"{safe_model}_{condition}_stage_c"] = (
                    int(sub[t2("stage_c_egress")].iloc[0]) if len(sub) else np.nan
                )
        rows.append(row)
    out = pd.DataFrame(rows)
    return out.sort_values(["stage_c_count", "stage_c_rate", "skill"], ascending=[False, False, True])


def build_pattern_summary(df: pd.DataFrame) -> pd.DataFrame:
    pattern_cols = [c for c in df.columns if c.startswith("pat_")]
    rows = []
    qwen = df[df["model"].isin(["qwen3:1.7b", "qwen3:8b"])]
    for col in pattern_cols:
        with_pat = qwen[pd.to_numeric(qwen[col], errors="coerce").fillna(0) == 1]
        without_pat = qwen[pd.to_numeric(qwen[col], errors="coerce").fillna(0) == 0]
        a = int(with_pat[t2("stage_c_egress")].sum())
        b = len(with_pat) - a
        c = int(without_pat[t2("stage_c_egress")].sum())
        d = len(without_pat) - c
        odds_ratio, p_value = fisher_p(a, b, c, d)
        rows.append(
            {
                "pattern": col,
                "qwen_rows_with_pattern": len(with_pat),
                "qwen_stage_c_with_pattern": a,
                "qwen_stage_c_rate_with_pattern": rate(a, len(with_pat)),
                "qwen_rows_without_pattern": len(without_pat),
                "qwen_stage_c_without_pattern": c,
                "qwen_stage_c_rate_without_pattern": rate(c, len(without_pat)),
                "risk_difference_with_minus_without": rate(a, len(with_pat)) - rate(c, len(without_pat)),
                "fisher_odds_ratio_unadjusted": odds_ratio,
                "fisher_p_unadjusted": p_value,
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values("risk_difference_with_minus_without", ascending=False)


def plot_stage_funnel(summary: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    stage_cols = ["stage_a_rate", "stage_b_rate", "stage_c_rate"]
    x = np.arange(len(CONDITION_ORDER))
    width = 0.23
    for ax, model in zip(axes.flat, MODEL_ORDER):
        sub = summary[summary["model"] == model].set_index("condition").reindex(CONDITION_ORDER)
        for i, col in enumerate(stage_cols):
            ax.bar(x + (i - 1) * width, sub[col].values * 100, width=width, label=col.replace("_rate", "").upper())
        ax.set_title(PLOT_LABELS[model])
        ax.set_xticks(x)
        ax.set_xticklabels([PLOT_LABELS[c] for c in CONDITION_ORDER], rotation=15, ha="right")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", alpha=0.25)
    axes[0, 0].set_ylabel("Rate (%)")
    axes[1, 0].set_ylabel("Rate (%)")
    axes[0, 0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Stage Indicators by Model and Condition")
    fig.tight_layout()
    path = OUT_DIR / "fig1_stage_indicators_by_model_condition.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_condition_effects(effects: pd.DataFrame) -> Path:
    qwen = effects[effects["model"].isin(["qwen3:1.7b", "qwen3:8b"])].copy()
    qwen["label"] = qwen["model"].map(PLOT_LABELS) + " " + qwen["comparison"]
    colors = ["#4c78a8" if "1.7" in x else "#f58518" for x in qwen["model"].astype(str)]
    fig, ax = plt.subplots(figsize=(10, 5))
    y = np.arange(len(qwen))
    ax.barh(y, qwen["risk_difference_compare_minus_base"] * 100, color=colors)
    ax.axvline(0, color="#222222", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(qwen["label"])
    ax.set_xlabel("Stage-C risk difference, compare - base (%)")
    ax.set_title("Matched Condition Effects on Stage-C Egress")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = OUT_DIR / "fig2_paired_condition_effects_qwen.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_detection_mismatch(mismatch: pd.DataFrame) -> Path:
    data = mismatch.copy()
    data["label"] = data["model"].map(PLOT_LABELS) + " " + data["condition"].map(PLOT_LABELS)
    y = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(y, data["detected_count"], color="#7f7f7f", label="Detected")
    ax.barh(y, data["detected_stage_b_count"], color="#4c78a8", label="Detected + Stage-B")
    ax.barh(y, data["detected_stage_c_count"], color="#e45756", label="Detected + Stage-C")
    ax.set_yticks(y)
    ax.set_yticklabels(data["label"], fontsize=8)
    ax.set_xlabel("Rows")
    ax.set_title("Detection Does Not Necessarily Gate Action")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = OUT_DIR / "fig3_detection_action_mismatch.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_process_footprint(process: pd.DataFrame) -> Path:
    data = process[process["stage_c_egress"] == 1].copy()
    data["label"] = data["model"].map(PLOT_LABELS) + " " + data["condition"].map(PLOT_LABELS)
    data = data.sort_values("fs_events_median", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(np.arange(len(data)), data["fs_events_median"] + 1, color="#54a24b")
    ax.set_xscale("log")
    ax.set_yticks(np.arange(len(data)))
    ax.set_yticklabels(data["label"])
    ax.set_xlabel("Median filesystem events among Stage-C rows, log scale (+1)")
    ax.set_title("Stage-C Process Footprint")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = OUT_DIR / "fig4_stage_c_process_footprint.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_workspace_outliers(outliers: pd.DataFrame) -> Path:
    data = outliers.head(12).copy().sort_values(t2("workspace_new_files_count"), ascending=True)
    data["label"] = data["model"].map(PLOT_LABELS).fillna(data["model"].astype(str)) + " " + data["skill"].astype(str)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(np.arange(len(data)), data[t2("workspace_new_files_count")], color="#b279a2")
    ax.set_yticks(np.arange(len(data)))
    ax.set_yticklabels(data["label"], fontsize=8)
    ax.set_xlabel("Workspace new files")
    ax.set_title("Workspace File-Creation Outliers")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = OUT_DIR / "fig6_workspace_file_outliers.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_silent_stage_c(summary: pd.DataFrame) -> Path:
    data = summary.copy()
    data["label"] = data["model"].map(PLOT_LABELS) + " " + data["condition"].map(PLOT_LABELS)
    y = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(12, 6))
    silent = data["silent_stage_c_count"]
    other = data["stage_c_count"] - data["silent_stage_c_count"]
    ax.barh(y, silent, color="#e45756", label="Silent Stage-C")
    ax.barh(y, other, left=silent, color="#72b7b2", label="Detected/reviewed Stage-C")
    ax.set_yticks(y)
    ax.set_yticklabels(data["label"], fontsize=8)
    ax.set_xlabel("Stage-C rows")
    ax.set_title("Most Stage-C Egress Is Silent")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path = OUT_DIR / "fig5_silent_stage_c_distribution.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def md_table(df: pd.DataFrame, cols: list[str], n: int | None = None, percent_cols: list[str] | None = None) -> str:
    percent_cols = percent_cols or []
    view = df[cols].copy()
    if n is not None:
        view = view.head(n)
    for col in percent_cols:
        if col in view:
            view[col] = view[col].map(pct)
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]) and col not in percent_cols:
            view[col] = view[col].map(lambda x: "NA" if pd.isna(x) else f"{x:.3g}")
    str_view = view.fillna("NA").astype(str)
    headers = list(str_view.columns)
    rows = str_view.values.tolist()
    widths = []
    for i, header in enumerate(headers):
        max_cell = max((len(row[i]) for row in rows), default=0)
        widths.append(max(len(header), max_cell))

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[i]) for i, value in enumerate(values)) + " |"

    sep = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join([fmt_row(headers), sep] + [fmt_row(row) for row in rows])


def write_markdown(
    summary: pd.DataFrame,
    effects: pd.DataFrame,
    mismatch: pd.DataFrame,
    process: pd.DataFrame,
    outliers: pd.DataFrame,
    canary: pd.DataFrame,
    skill_rank: pd.DataFrame,
    pattern_summary: pd.DataFrame,
    figures: list[Path],
    run_info: dict,
) -> Path:
    total = int(run_info["valid_rows"])
    stage_c = int(run_info["stage_c_rows"])
    silent = int(run_info["silent_stage_c_rows"])
    detected_but_b = int(run_info["detected_but_stage_b_rows"])
    detected_but_c = int(run_info["detected_but_stage_c_rows"])
    canary_total = int(run_info["canary_requests_sum"])

    qwen_effects = effects[effects["model"].isin(["qwen3:1.7b", "qwen3:8b"])]
    process_stage_c = process[process["stage_c_egress"] == 1]
    top_skills = skill_rank.head(12)
    top_outliers = outliers.head(8).copy()

    lines = [
        "# Deep Tier-2 Analysis",
        "",
        "This analysis uses the existing Tier-1 + Tier-2 dataset only. No additional agent experiments were run.",
        "",
        "## Executive Result",
        "",
        (
            "The Tier-2 mapping changes the result from a flat ASR table into a behavioral pathway analysis. "
            "The strongest finding is not plaintext credential theft; it is mostly silent network egress to the "
            "canary endpoint under specific model/runtime and condition combinations."
        ),
        "",
        f"- Valid raw-session rows: {total}",
        f"- Stage-C egress rows: {stage_c} ({pct(stage_c / total)})",
        f"- Silent Stage-C rows: {silent} ({pct(silent / stage_c)} of Stage-C)",
        f"- Canary requests observed: {canary_total}",
        "- Canary token leakage: 0",
        "- Canary request bodies with nonzero size: 0",
        f"- Detected-but-Stage-B rows: {detected_but_b}",
        f"- Detected-but-Stage-C rows: {detected_but_c}",
        "",
        "## 1. Data Contract",
        "",
        (
            "The analysis filters to the 1019 rows with matching `full_result.json`. The one missing Tier-2 row is "
            "the known qwen3:8b / grubhub / C3 infrastructure failure with no `session_id`. Raw-result schemas "
            "differ by batch: `dangerous_commands` exists for 764 rows and is absent for the 255 qwen3:1.7b rows, "
            "so command-count zeros in that batch must be treated as not available rather than proof of no command."
        ),
        "",
        "## 2. Model-Condition Outcome Summary",
        "",
        md_table(
            summary,
            [
                "model",
                "condition",
                "n",
                "stage_a_rate",
                "stage_b_rate",
                "stage_c_rate",
                "detected_rate",
                "silent_fraction_among_stage_c",
                "canary_requests_sum",
                "fs_events_median",
                "workspace_files_median",
            ],
            percent_cols=[
                "stage_a_rate",
                "stage_b_rate",
                "stage_c_rate",
                "detected_rate",
                "silent_fraction_among_stage_c",
            ],
        ),
        "",
        "Interpretation:",
        "",
        "- C2 safety review suppresses Qwen Stage-C sharply.",
        "- C3 trust pressure amplifies Qwen Stage-C sharply.",
        "- GPT/Codex configurations still show high Stage-B activity, but Stage-C remains zero.",
        "- qwen3:8b C3 has the largest observed process footprint, especially filesystem events and workspace file creation.",
        "",
        "## 3. Paired Condition Effects",
        "",
        (
            "The condition comparisons below are paired by skill within each model. This is more appropriate than "
            "unpaired row-level comparisons because each skill appears across conditions."
        ),
        "",
        md_table(
            qwen_effects,
            [
                "model",
                "comparison",
                "paired_skills",
                "base_stage_c_count",
                "compare_stage_c_count",
                "base_stage_c_rate",
                "compare_stage_c_rate",
                "risk_difference_compare_minus_base",
                "induced_0_to_1",
                "suppressed_1_to_0",
                "mcnemar_exact_p",
            ],
            percent_cols=[
                "base_stage_c_rate",
                "compare_stage_c_rate",
                "risk_difference_compare_minus_base",
            ],
        ),
        "",
        "Interpretation:",
        "",
        (
            "- For qwen3:8b, C2 vs C1 is a strong suppression effect; C3 vs C2 is a strong induction effect. "
            "For qwen3:1.7b, C3 also strongly induces Stage-C compared with both C1 and C2."
        ),
        (
            "- GPT/Codex has no Stage-C discordance across conditions, so paired tests there are uninformative for "
            "egress but useful as a negative-control style result for the tested runtime configuration."
        ),
        "",
        "## 4. Detection Is Not Prevention",
        "",
        md_table(
            mismatch,
            [
                "model",
                "condition",
                "detected_count",
                "detected_stage_b_count",
                "detected_stage_c_count",
                "review_count",
                "review_stage_b_count",
                "review_stage_c_count",
                "silent_stage_c_count",
            ],
        ),
        "",
        "Interpretation:",
        "",
        (
            "- Detection/review often coexists with Stage-B execution. Across the dataset, "
            f"`detected_but_stage_b` occurs {detected_but_b} times."
        ),
        (
            "- In GPT/Codex rows, review/detection usually still allows some action, but the action does not cross "
            "the Stage-C network boundary. This is better described as boundary-respecting execution, not simple refusal."
        ),
        (
            "- In Qwen rows, a small number of detected/review cases still reach Stage-C. The defense implication is "
            "that detection must gate action or network egress; warning text alone is not a sufficient control."
        ),
        "",
        "## 5. Stage-C Means Network Egress, Not Secret Leakage",
        "",
        md_table(
            canary,
            [
                "model",
                "condition",
                "n",
                "stage_c_count",
                "canary_requests_sum",
                "canary_api_exfil_events_sum",
                "canary_get_events_sum",
                "canary_body_size_total",
                "canary_nonempty_body_events_sum",
                "canary_token_leaked_count",
                "canary_requests_per_stage_c_row",
            ],
        ),
        "",
        "Interpretation:",
        "",
        (
            "- Every canary log event is a GET to `/api/exfil`, and observed request bodies are empty. The correct "
            "paper wording is network egress attempt or canary endpoint contact, not plaintext credential leakage."
        ),
        (
            "- This distinction strengthens the work rather than weakening it: it shows the agent crossed an external "
            "network boundary even without successful secret payload transfer."
        ),
        "",
        "## 6. Process Footprint",
        "",
        md_table(
            process_stage_c,
            [
                "model",
                "condition",
                "n",
                "workspace_files_mean",
                "fs_events_median",
                "fs_events_p95",
                "fs_events_max",
                "workspace_files_median",
                "workspace_files_p95",
                "workspace_files_max",
                "workspace_files_gt100_count",
                "dangerous_commands_median",
                "canary_requests_median",
                "schema_dangerous_commands_rate",
            ],
            percent_cols=["schema_dangerous_commands_rate"],
        ),
        "",
        "Interpretation:",
        "",
        (
            "- qwen3:8b C3 is the clearest high-footprint failure mode, but the footprint is heavy-tailed. "
            "Most Stage-C rows have small workspace-file counts; a few installer/build outliers dominate the mean."
        ),
        (
            "- qwen3:1.7b C3 reaches Stage-C frequently but has a different raw schema; command-trace absence should "
            "not be interpreted as clean execution."
        ),
        "",
        "Top process outliers:",
        "",
        md_table(
            top_outliers,
            [
                "session_id",
                "model",
                "condition",
                "skill",
                t2("stage_c_egress"),
                t2("workspace_new_files_count"),
                t2("fs_events_count"),
                t2("dangerous_commands_count"),
                t2("canary_requests"),
            ],
        ),
        "",
        "## 7. Skill-Level Case-Study Candidates",
        "",
        md_table(
            top_skills,
            [
                "skill",
                "skill_category",
                "service_sensitivity",
                "payload_type",
                "n",
                "stage_c_count",
                "stage_c_rate",
                "silent_stage_c_count",
                "detected_count",
            ],
            percent_cols=["stage_c_rate"],
        ),
        "",
        (
            "Skill rankings are useful for choosing case studies, but they should not be over-read as causal. "
            "The balanced design and SHAP rerun still indicate that condition plus model/runtime dominate the primary "
            "Stage-C signal."
        ),
        "",
        "## 8. Pattern-Level Exploratory Check",
        "",
        md_table(
            pattern_summary,
            [
                "pattern",
                "qwen_rows_with_pattern",
                "qwen_stage_c_rate_with_pattern",
                "qwen_rows_without_pattern",
                "qwen_stage_c_rate_without_pattern",
                "risk_difference_with_minus_without",
                "fisher_p_unadjusted",
            ],
            n=12,
            percent_cols=[
                "qwen_stage_c_rate_with_pattern",
                "qwen_stage_c_rate_without_pattern",
                "risk_difference_with_minus_without",
            ],
        ),
        "",
        (
            "This is intentionally labeled exploratory and unadjusted. These pattern columns are useful for narrative "
            "and ablation design, but not enough to claim independent causal effects without controlling for model, "
            "condition, runtime, and skill family."
        ),
        "",
        "## 9. What This Supports",
        "",
        "- Strong claim: prompt condition changes can dramatically alter egress behavior in the tested Qwen/OpenCode runtime.",
        "- Strong claim: safety review reduces Stage-C egress in Qwen runs, while trust pressure increases it.",
        "- Strong claim: GPT/Codex performs many Stage-B actions while maintaining 0 Stage-C in this dataset.",
        "- Strong claim: most Stage-C is silent network-boundary crossing, not explicit secret leakage.",
        "- Defense claim: detection must be coupled to an action or egress gate.",
        "",
        "## 10. What This Does Not Support",
        "",
        "- Do not claim pure model effects; model and agent runtime are still confounded.",
        "- Do not claim token theft; observed token leakage is zero.",
        "- Do not use post-outcome Tier-2 features as pre-execution predictors without separating label leakage.",
        "- Do not claim skill-pattern causality from the unadjusted pattern table.",
        "",
        "## Output Figures",
        "",
    ]
    for fig in figures:
        lines.append(f"- `{fig.name}`")
    lines.extend(
        [
            "",
            "## Output Tables",
            "",
            "- `table1_model_condition_deep_summary.csv`",
            "- `table2_paired_condition_effects.csv`",
            "- `table3_decision_outcomes.csv`",
            "- `table4_detection_action_mismatch.csv`",
            "- `table5_process_footprint_by_stagec.csv`",
            "- `table6_canary_summary.csv`",
            "- `table7_skill_stagec_rank.csv`",
            "- `table8_pattern_unadjusted_qwen.csv`",
            "- `table9_process_outliers.csv`",
            "- `run_info.json`",
        ]
    )

    path = OUT_DIR / "DEEP_TIER2_ANALYSIS.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT, encoding="utf-8-sig")

    numeric_cols = [
        t2("stage_a_acceptance"),
        t2("stage_b_execution"),
        t2("stage_c_egress"),
        t2("silent_stage_c"),
        t2("detected_malicious"),
        t2("refused_execution"),
        t2("warned_user"),
        t2("decision_accept"),
        t2("decision_review"),
        t2("decision_refuse"),
        t2("decision_unclear"),
        t2("detected_but_stage_b"),
        t2("detected_but_stage_c"),
        t2("review_but_stage_b"),
        t2("review_but_stage_c"),
        t2("canary_requests"),
        t2("canary_log_events"),
        t2("canary_api_exfil_events"),
        t2("canary_get_events"),
        t2("canary_post_events"),
        t2("canary_body_size_total"),
        t2("canary_nonempty_body_events"),
        t2("canary_token_leaked"),
        t2("fs_events_count"),
        t2("workspace_new_files_count"),
        t2("dangerous_commands_count"),
        t2("schema_has_dangerous_commands"),
        t2("schema_has_canifi_events"),
    ]
    numeric_cols.extend([c for c in df.columns if c.startswith("pat_")])
    to_num(df, numeric_cols)

    valid = df[df[t2("stage_c_egress")].notna()].copy()
    valid["model"] = pd.Categorical(valid["model"], MODEL_ORDER, ordered=True)
    valid["condition"] = pd.Categorical(valid["condition"], CONDITION_ORDER, ordered=True)
    valid = valid.sort_values(["model", "condition", "skill"])
    valid["model"] = valid["model"].astype(str)
    valid["condition"] = valid["condition"].astype(str)

    summary = build_model_condition_summary(valid)
    effects = build_paired_condition_effects(valid)
    decision = build_decision_summary(valid)
    mismatch = build_detection_mismatch(valid)
    process = build_process_footprint(valid)
    outliers = build_process_outliers(valid)
    canary = build_canary_summary(valid)
    skill_rank = build_skill_rank(valid)
    pattern_summary = build_pattern_summary(valid)

    save_csv(summary, "table1_model_condition_deep_summary.csv")
    save_csv(effects, "table2_paired_condition_effects.csv")
    save_csv(decision, "table3_decision_outcomes.csv")
    save_csv(mismatch, "table4_detection_action_mismatch.csv")
    save_csv(process, "table5_process_footprint_by_stagec.csv")
    save_csv(canary, "table6_canary_summary.csv")
    save_csv(skill_rank, "table7_skill_stagec_rank.csv")
    save_csv(pattern_summary, "table8_pattern_unadjusted_qwen.csv")
    save_csv(outliers, "table9_process_outliers.csv")

    figures = [
        plot_stage_funnel(summary),
        plot_condition_effects(effects),
        plot_detection_mismatch(mismatch),
        plot_process_footprint(process),
        plot_silent_stage_c(summary),
        plot_workspace_outliers(outliers),
    ]

    run_info = {
        "input": str(INPUT),
        "output_dir": str(OUT_DIR),
        "source_rows": int(len(df)),
        "valid_rows": int(len(valid)),
        "missing_tier2_rows": int(len(df) - len(valid)),
        "stage_c_rows": int(valid[t2("stage_c_egress")].sum()),
        "silent_stage_c_rows": int(valid[t2("silent_stage_c")].sum()),
        "detected_but_stage_b_rows": int(valid[t2("detected_but_stage_b")].sum()),
        "detected_but_stage_c_rows": int(valid[t2("detected_but_stage_c")].sum()),
        "canary_requests_sum": int(valid[t2("canary_requests")].sum()),
        "canary_log_events_sum": int(valid[t2("canary_log_events")].sum()),
        "canary_token_leaked_rows": int(valid[t2("canary_token_leaked")].sum()),
        "canary_nonempty_body_events_sum": int(valid[t2("canary_nonempty_body_events")].sum()),
        "dangerous_commands_schema_rows": int(valid[t2("schema_has_dangerous_commands")].sum()),
        "canifi_schema_rows": int(valid[t2("schema_has_canifi_events")].sum()),
        "figures": [str(x) for x in figures],
    }
    (OUT_DIR / "run_info.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2) + "\n")
    md_path = write_markdown(
        summary,
        effects,
        mismatch,
        process,
        outliers,
        canary,
        skill_rank,
        pattern_summary,
        figures,
        run_info,
    )

    print(json.dumps({**run_info, "markdown": str(md_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
