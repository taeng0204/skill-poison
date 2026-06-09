# SkillProbe Visualizations

This directory contains standalone visual artifacts generated from the released
CSV and normalized `full_result.json` data. No additional agent experiments are
run.

## `session_behavior_map.html`

Interactive run-level evidence map over
`artifacts/tier2_features/merged_runs_features_tier1_tier2.csv`.

The map encodes:

- model by color,
- condition by opacity,
- sessions by row,
- behavioral evidence features by cell.

Important limitation: this is not a turn-by-turn timeline. The released
`full_result.json` records do not contain full LLM conversation transcripts,
complete tool-call traces, or per-action timestamps. The visualization therefore
shows run-level evidence such as Stage-B execution, Stage-C canary egress,
command evidence, URL/domain observations, filesystem effects, and
detection-action gaps.

Regenerate:

```bash
python3 build_session_behavior_map.py
```
