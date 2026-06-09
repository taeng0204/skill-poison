# Raw Session Provenance

This directory standardizes raw `full_result.json` records for the final
1020-row clean summary dataset.

## Contents

- `sessions/<session_id>/full_result.json`: 1019 raw session records.
- `provenance.csv`: one row per summary CSV row, with source and artifact path.
- `provenance_summary.json`: aggregate coverage summary.

## Coverage

The final clean summary has 1020 rows. Of those, 1019 have matching raw
`full_result.json` records.

The only unmatched row is not a completed session:

```text
model: qwen3:8b
skill: grubhub
condition: C3
status: error
error: Port could not be cast to integer value as 'canifi'
```

That row has no `session_id` and should be excluded from ASR/XAI denominators.

## Sources

The normalized files were copied from:

- local `experiment/runner/results/*/full_result.json`
- `full_results_only_20260601.zip`
- `full_result_json_255_20260608_194523.zip`
