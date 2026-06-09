# Tier-2 Process Features

These artifacts are derived only from existing normalized `full_result.json`
records. No additional agent experiments were run.

## Inputs

- Raw sessions: `artifacts/full_results/sessions`
- Tier-1 dataset: `merged_runs_features_tier1.csv`

## Outputs

- `tier2_process_features.csv`: one row per raw session with process, canary,
  filesystem, URL, command, and detection features.
- `merged_runs_features_tier1_tier2.csv`: Tier-1 rows left-joined with Tier-2
  features by `session_id`.
- `tier2_summary_by_model_condition.csv`: descriptive model-condition summary.
- `tier2_decision_outcomes.csv`: decision-class outcome summary.
- `tier2_top_domains.csv`: top observed external domains.
- `TIER2_FINDINGS.md`: concise interpretation of the extracted features.
- `run_info.json`: row counts and join coverage.

## Coverage

- Raw Tier-2 rows: 1019
- Tier-1 rows: 1020
- Matched Tier-1/Tier-2 rows: 1019
- Missing Tier-2 rows: 1

The expected missing row is the qwen3:8b / grubhub / C3 infrastructure error
that has no `session_id` and no raw completed session.

## Interpretation Notes

Tier-2 features are execution-observation features, not new labels. They help
explain how Stage-C egress happened: command traces, canary requests,
workspace file explosion, URL domains, and detection/action inconsistencies.
They should be used alongside the Tier-1 condition/model/skill features, not as
a replacement for the original experimental design.

Some raw-result schemas differ by run batch. In particular, `dangerous_commands`
is present for 764 rows and absent for the 255 qwen3:1.7b rows. Use
`schema_has_*` columns to distinguish "not observed" from "not available."
