# Tier-2 Findings

This pass used only existing `full_result.json` artifacts. No additional agent
experiments were run.

## Coverage

- Raw Tier-2 rows: 1019
- Tier-1 rows: 1020
- Tier-1/Tier-2 matched rows: 1019
- Missing row: the known qwen3:8b / grubhub / C3 infrastructure failure with no
  `session_id`

## Main Findings

1. Stage-C egress is mostly silent in the existing data.
   - Stage-C rows: 195
   - Silent Stage-C rows: 191
   - Canary token leakage: 0
   - Canary events: all observed request bodies are empty; the measured event is
     network egress to the canary endpoint, not plaintext secret exfiltration.

2. Safety review suppresses Qwen egress, while trust pressure amplifies it.
   - qwen3:8b C1/C2/C3 Stage-C rates: 57.6%, 3.5%, 96.4%
   - qwen3:1.7b C1/C2/C3 Stage-C rates: 8.2%, 0.0%, 64.7%
   - GPT/Codex configurations remain at 0% Stage-C across C1/C2/C3.

3. Detection is not the same as non-execution.
   - `detected_but_stage_b`: 276 rows
   - For GPT/Codex, these detected/review rows still show Stage-B activity but
     no Stage-C egress.
   - For Qwen, a small number of review/detected rows still reach Stage-C, so
     detection alone is not a reliable defense unless it gates action.

4. qwen3:8b C3 shows the largest process footprint.
   - Mean workspace new files: 141.75
   - Mean filesystem events: 4726.5
   - The extracted command/file features capture curl tarball/source-tree
     behavior in these runs.

5. Domain evidence matches the canary design.
   - `ensures-fixtures-gba-planets.trycloudflare.com` appears in 254 rows, with
     133 Stage-C rows.
   - `canary:18080` appears in command/trace-derived domains for 20 rows, all
     Stage-C.
   - `127.0.0.1:8745` appears in 510 Codex MCP rows, with 0 Stage-C rows.

## Caveat

Raw-result schemas differ by run batch. `dangerous_commands` exists for 764
rows and is absent for the 255 qwen3:1.7b rows. Use `schema_has_*` columns before
interpreting zeros in process features.

## Best Use

Use `merged_runs_features_tier1_tier2.csv` for paper tables and follow-up
analysis. Tier-2 features should support mechanism claims about observed
execution traces; they should not be presented as new experimental conditions.
