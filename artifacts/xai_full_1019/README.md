# Full-Data XAI Rerun

This directory contains a SHAP/XAI rerun over the 1019 rows with non-missing
`stage_c_egress` in `merged_runs_features_tier1.csv`.

## Command

```bash
python3 xai_shap_analysis.py \
  --input merged_runs_features_tier1.csv \
  --output-dir artifacts/xai_full_1019 \
  --models logistic random_forest \
  --test-size 0.25
```

## Metrics

| Model | Accuracy | F1 | ROC-AUC | Average Precision |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.914 | 0.807 | 0.963 | 0.828 |
| Random Forest | 0.925 | 0.829 | 0.970 | 0.876 |

## Interpretation

The full-data rerun preserves the earlier conclusion: condition and
model/runtime metadata dominate Stage-C egress prediction. Skill attack-pattern
features are weaker auxiliary signals and should not be over-claimed as causal.
