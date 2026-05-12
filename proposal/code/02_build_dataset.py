"""
Merge 3 condition CSVs + skill features into a unified dataset.
Output: dataset.csv with one row per (condition, model, skill).
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "docs"
HERE = Path(__file__).parent

CONDITION_FILES = {
    "listing-only": ROOT / "summary.csv",
    "trust-badge": ROOT / "summary1.csv",
    "task-driven": ROOT / "summary2.csv",
}

# Macro (condition-level) features — reflect what eval.py actually changed
CONDITION_MACRO = {
    "listing-only": dict(setup_visible=0, trust_badge=0, task_context=0),
    "trust-badge": dict(setup_visible=0, trust_badge=1, task_context=0),
    "task-driven": dict(setup_visible=0, trust_badge=0, task_context=1),
}


def main():
    skill_feat = pd.read_csv(HERE / "skill_features.csv")

    frames = []
    for cond, path in CONDITION_FILES.items():
        df = pd.read_csv(path)
        df["condition"] = cond
        for k, v in CONDITION_MACRO[cond].items():
            df[k] = v
        frames.append(df)

    big = pd.concat(frames, ignore_index=True)
    big = big.merge(skill_feat, on="skill_name", how="left")

    # binary label
    big["accept"] = (big["decision"] == "accept").astype(int)

    out = HERE / "dataset.csv"
    big.to_csv(out, index=False)
    print(f"Wrote {len(big)} rows × {len(big.columns)} cols to {out}")
    print(f"\nLabel balance: {big['accept'].mean():.3f} accept rate overall")
    print("\nAccept rate by condition × model:")
    print(big.groupby(["condition", "model"])["accept"].mean().round(3).unstack())


if __name__ == "__main__":
    main()
