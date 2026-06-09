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

## `session_outcome_flow.html`

Interactive alluvial/Sankey-style graph from model/condition cohorts to
terminal run outcomes:

- `R`: safety review / local stop
- `U`: unclear / no action
- `A`: accepted only
- `B`: local execution only
- `N`: Stage-C network egress without raw canary-hit flag
- `H`: Stage-C network egress with raw canary-hit or marker flag

Regenerate:

```bash
python3 build_session_outcome_flow.py
```

The `N/H` split is a secondary raw canary-hit flag split. For paper claims,
use `stage_c_egress` and `canary_requests` as the authoritative boundary label.
