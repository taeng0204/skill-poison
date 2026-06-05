from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_INPUT = Path(
    r"C:\Users\user\Documents\Codex\2026-05-07\codex\outputs\merged_runs_features_tier1_qwen3_1_7b_replaced.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    r"C:\Users\user\Documents\Codex\2026-05-07\codex\outputs\xai_shap"
)

TARGET_COLUMN = "stage_c_egress"

# Excluded columns are post-outcome signals, identifiers, or bookkeeping.
EXCLUDE_COLUMNS = {
    "session_id",
    "status",
    "exit_code",
    "duration_s",
    "stage_a_acceptance",
    "stage_b_execution",
    "stage_c_egress",
    "canary_requests",
    "canary_hit",
    "canary_token_leaked",
    "agent_refused",
    "agent_detected_malicious",
    "task_completed",
    "error",
}

PREFERRED_FEATURES = [
    "condition",
    "model",
    "skill_category",
    "service_sensitivity",
    "service_sensitivity_ord",
    "n_credential_vars",
    "n_risk_keywords",
    "has_rce",
    "has_env_exfil",
    "payload_type",
    "skill_len_chars",
    "n_code_blocks",
    "n_steps",
    "model_family",
    "model_size_b",
    "model_tier",
    "alignment_tier",
    "trust_pressure",
    "safety_review",
    "condition_label",
    "hf_classification",
    "hf_source",
    "n_attack_patterns",
    "pat_rce",
    "pat_cred_theft",
    "pat_behavior_manip",
    "pat_ext_transmission",
    "pat_context_leakage",
    "pat_hidden_instr",
    "pat_code_obfusc",
    "pat_instr_override",
    "pat_excess_perms",
    "pat_hardcoded_tokens",
    "pat_fs_scan",
    "pat_data_exfil",
]


def require_packages() -> None:
    missing = []
    for pkg, import_name in [
        ("scikit-learn", "sklearn"),
        ("shap", "shap"),
        ("matplotlib", "matplotlib"),
    ]:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("Missing packages:", ", ".join(missing), file=sys.stderr)
        print(
            "Install in PowerShell with:\n"
            "  py -m pip install pandas scikit-learn shap matplotlib openpyxl\n"
            "\nOptional CatBoost model:\n"
            "  py -m pip install catboost",
            file=sys.stderr,
        )
        sys.exit(1)


def parse_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
        }
    )


def load_dataset(input_path: Path) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    df = pd.read_csv(input_path)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")

    y_bool = parse_bool_series(df[TARGET_COLUMN])
    keep_mask = y_bool.notna()
    dropped = int((~keep_mask).sum())
    df = df.loc[keep_mask].copy()
    y = y_bool.loc[keep_mask].astype(int)

    feature_cols = [
        col
        for col in PREFERRED_FEATURES
        if col in df.columns and col not in EXCLUDE_COLUMNS
    ]
    if not feature_cols:
        raise ValueError("No usable feature columns found.")

    X = df[feature_cols].copy()

    bool_like = [
        "has_rce",
        "has_env_exfil",
        "trust_pressure",
        "safety_review",
        "pat_rce",
        "pat_cred_theft",
        "pat_behavior_manip",
        "pat_ext_transmission",
        "pat_context_leakage",
        "pat_hidden_instr",
        "pat_code_obfusc",
        "pat_instr_override",
        "pat_excess_perms",
        "pat_hardcoded_tokens",
        "pat_fs_scan",
        "pat_data_exfil",
    ]
    for col in bool_like:
        if col in X.columns:
            parsed = parse_bool_series(X[col])
            if parsed.notna().any():
                X[col] = parsed.astype("float")

    print(f"Loaded {len(df)} usable rows from {input_path}")
    if dropped:
        print(f"Dropped {dropped} row(s) with missing target.")
    print(f"Target positive rate: {y.mean():.3f} ({int(y.sum())}/{len(y)})")
    print(f"Feature columns ({len(feature_cols)}): {feature_cols}")
    return X, y, feature_cols


def make_preprocessor(X: pd.DataFrame, scale_numeric: bool):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    numeric_cols = []
    categorical_cols = []
    for col in X.columns:
        converted = pd.to_numeric(X[col], errors="coerce")
        non_missing = X[col].notna().sum()
        if non_missing and converted.notna().sum() == non_missing:
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)

    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)

    numeric_steps = [SimpleImputer(strategy="median")]
    if scale_numeric:
        numeric_steps.append(StandardScaler())

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", make_pipeline(SimpleImputer(strategy="most_frequent"), encoder), categorical_cols),
            ("num", make_pipeline(*numeric_steps), numeric_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor, categorical_cols, numeric_cols


def feature_names(preprocessor) -> list[str]:
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        return [f"feature_{i}" for i in range(preprocessor.transformers_[0][1].shape[1])]


def positive_class_shap_values(raw_values):
    values = np.asarray(raw_values)
    if values.ndim == 3:
        return values[:, :, 1]
    if isinstance(raw_values, list) and len(raw_values) == 2:
        return raw_values[1]
    return values


def save_shap_outputs(model_name: str, shap_values, X_sample, names: list[str], output_dir: Path) -> pd.DataFrame:
    import matplotlib.pyplot as plt
    import shap

    output_dir.mkdir(parents=True, exist_ok=True)
    shap_arr = positive_class_shap_values(shap_values)
    importance = pd.DataFrame(
        {
            "feature": names,
            "mean_abs_shap": np.abs(shap_arr).mean(axis=0),
            "mean_shap": shap_arr.mean(axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False)

    importance_path = output_dir / f"shap_importance_{model_name}.csv"
    importance.to_csv(importance_path, index=False, encoding="utf-8-sig")

    explanation = shap.Explanation(
        values=shap_arr,
        data=X_sample,
        feature_names=names,
    )

    plt.figure()
    shap.plots.bar(explanation, max_display=25, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / f"shap_bar_{model_name}.png", dpi=180, bbox_inches="tight")
    plt.close()

    plt.figure()
    shap.plots.beeswarm(explanation, max_display=25, show=False)
    plt.tight_layout()
    plt.savefig(output_dir / f"shap_beeswarm_{model_name}.png", dpi=180, bbox_inches="tight")
    plt.close()

    return importance


def fit_logistic(X_train, X_test, y_train, y_test, output_dir: Path):
    import shap
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
    from sklearn.pipeline import make_pipeline

    preprocessor, _, _ = make_preprocessor(X_train, scale_numeric=True)
    clf = LogisticRegression(max_iter=5000, class_weight="balanced", random_state=42)
    pipe = make_pipeline(preprocessor, clf)
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "model": "logistic_regression",
        "accuracy": accuracy_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
        "average_precision": average_precision_score(y_test, proba),
    }

    pre = pipe.named_steps["columntransformer"]
    estimator = pipe.named_steps["logisticregression"]
    X_train_t = pre.transform(X_train)
    X_test_t = pre.transform(X_test)
    names = feature_names(pre)

    explainer = shap.LinearExplainer(estimator, X_train_t)
    shap_values = explainer.shap_values(X_test_t)
    importance = save_shap_outputs("logistic_regression", shap_values, X_test_t, names, output_dir)
    return metrics, importance


def fit_random_forest(X_train, X_test, y_train, y_test, output_dir: Path):
    import shap
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
    from sklearn.pipeline import make_pipeline

    preprocessor, _, _ = make_preprocessor(X_train, scale_numeric=False)
    clf = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    pipe = make_pipeline(preprocessor, clf)
    pipe.fit(X_train, y_train)

    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "model": "random_forest",
        "accuracy": accuracy_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
        "average_precision": average_precision_score(y_test, proba),
    }

    pre = pipe.named_steps["columntransformer"]
    estimator = pipe.named_steps["randomforestclassifier"]
    X_test_t = pre.transform(X_test)
    names = feature_names(pre)

    explainer = shap.TreeExplainer(estimator)
    shap_values = explainer.shap_values(X_test_t)
    importance = save_shap_outputs("random_forest", shap_values, X_test_t, names, output_dir)
    return metrics, importance


def fit_catboost(X_train, X_test, y_train, y_test, output_dir: Path):
    try:
        import catboost as cb
        import shap
        from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
    except ImportError:
        print("CatBoost is not installed. Install with: py -m pip install catboost")
        return None, None

    X_train_cb = X_train.copy()
    X_test_cb = X_test.copy()
    categorical_cols = []
    numeric_cols = []
    for col in X_train_cb.columns:
        converted = pd.to_numeric(X_train_cb[col], errors="coerce")
        non_missing = X_train_cb[col].notna().sum()
        if non_missing and converted.notna().sum() == non_missing:
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
    cat_indices = [X_train_cb.columns.get_loc(col) for col in categorical_cols]

    for col in categorical_cols:
        X_train_cb[col] = X_train_cb[col].fillna("__MISSING__").astype(str)
        X_test_cb[col] = X_test_cb[col].fillna("__MISSING__").astype(str)
    for col in numeric_cols:
        X_train_cb[col] = pd.to_numeric(X_train_cb[col], errors="coerce")
        X_test_cb[col] = pd.to_numeric(X_test_cb[col], errors="coerce")

    model = cb.CatBoostClassifier(
        iterations=500,
        depth=5,
        learning_rate=0.05,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=42,
        verbose=False,
        auto_class_weights="Balanced",
    )
    model.fit(X_train_cb, y_train, cat_features=cat_indices)

    proba = model.predict_proba(X_test_cb)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "model": "catboost",
        "accuracy": accuracy_score(y_test, pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
        "average_precision": average_precision_score(y_test, proba),
    }

    test_pool = cb.Pool(X_test_cb, cat_features=cat_indices)
    shap_values = model.get_feature_importance(test_pool, type="ShapValues")[:, :-1]
    importance = save_shap_outputs(
        "catboost",
        shap_values,
        X_test_cb.to_numpy(),
        list(X_test_cb.columns),
        output_dir,
    )
    return metrics, importance


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline models and run SHAP for Stage-C egress.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input CSV path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["logistic", "random_forest"],
        choices=["logistic", "random_forest", "catboost"],
        help="Models to train. Default: logistic random_forest",
    )
    parser.add_argument("--test-size", type=float, default=0.25)
    args = parser.parse_args()

    require_packages()

    from sklearn.model_selection import train_test_split

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    X, y, _ = load_dataset(Path(args.input))
    X.to_csv(output_dir / "xai_model_features_only.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({TARGET_COLUMN: y}).to_csv(output_dir / "xai_model_target.csv", index=False)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=42,
        stratify=y,
    )

    metrics = []
    if "logistic" in args.models:
        model_metrics, _ = fit_logistic(X_train, X_test, y_train, y_test, output_dir)
        metrics.append(model_metrics)
    if "random_forest" in args.models:
        model_metrics, _ = fit_random_forest(X_train, X_test, y_train, y_test, output_dir)
        metrics.append(model_metrics)
    if "catboost" in args.models:
        model_metrics, _ = fit_catboost(X_train, X_test, y_train, y_test, output_dir)
        if model_metrics:
            metrics.append(model_metrics)

    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")

    run_info = {
        "input": str(Path(args.input)),
        "output_dir": str(output_dir),
        "target": TARGET_COLUMN,
        "rows": int(len(X)),
        "positive_rows": int(y.sum()),
        "models": args.models,
    }
    (output_dir / "run_info.json").write_text(json.dumps(run_info, indent=2), encoding="utf-8")

    print("\nDone.")
    print(metrics_df.to_string(index=False))
    print(f"\nOutputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
