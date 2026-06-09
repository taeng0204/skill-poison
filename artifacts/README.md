# SkillProbe Artifacts

This directory contains normalized analysis artifacts that are derived from the
root experiment CSVs and raw session result ZIPs.

Start with `DATASET_CARD.md` for the release overview.

## `full_results/`

Raw session provenance for `merged_runs_features_tier1.csv`.

- `sessions/<session_id>/full_result.json`: normalized raw session records for
  1019 analysis-valid rows.
- `provenance.csv`: row-level mapping from each clean summary row to its raw
  `full_result.json` source.
- `provenance_summary.json`: aggregate provenance counts and the single excluded
  measurement-failure row.

Coverage:

- Summary rows: 1020
- Matched raw `full_result.json`: 1019
- Missing raw result: 1 measurement failure, `qwen3:8b / grubhub / C3`

## `xai_full_1019/`

Full-data XAI rerun using the 1019 rows with non-missing `stage_c_egress`.

Command:

```bash
python3 xai_shap_analysis.py \
  --input merged_runs_features_tier1.csv \
  --output-dir artifacts/xai_full_1019 \
  --models logistic random_forest \
  --test-size 0.25
```

The root-level XAI files were created from an earlier 764-row run. Use this
directory for final reporting.

## `tier2_features/`

Execution-process features extracted from the normalized raw `full_result.json`
records. These include command, filesystem, URL/domain, canary, decision, and
detection-action mismatch features.

Key files:

- `tier2_process_features.csv`: 1019 raw-session rows, one per `full_result.json`.
- `merged_runs_features_tier1_tier2.csv`: 1020 Tier-1 rows left-joined with
  Tier-2 features by `session_id`.
- `TIER2_FINDINGS.md`: concise findings from the extraction pass.

## `tier2_analysis/`

Deep analysis over the Tier-1 + Tier-2 dataset.

Key files:

- `DEEP_TIER2_ANALYSIS.md`: main mechanism analysis.
- `table*.csv`: model-condition, paired-condition, detection-action, canary,
  process-footprint, skill-rank, and exploratory pattern tables.
- `fig*.png`: report-ready figures.

## `figures/`

Report-ready descriptive figures from the final 1019-row analysis.
