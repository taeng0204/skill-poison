# Tier-2 Deep Analysis

This directory contains a deep analysis over the existing Tier-1 + Tier-2
dataset. No additional agent experiments were run.

## Start Here

- `DEEP_TIER2_ANALYSIS.md`: main interpretation document.
- `run_info.json`: row counts and validation summary.

## Tables

- `table1_model_condition_deep_summary.csv`: model-condition outcome summary.
- `table2_paired_condition_effects.csv`: skill-paired condition comparisons.
- `table3_decision_outcomes.csv`: outcome summary by decision class.
- `table4_detection_action_mismatch.csv`: detection/review vs Stage-B/Stage-C.
- `table5_process_footprint_by_stagec.csv`: process metrics split by Stage-C.
- `table6_canary_summary.csv`: canary request/body/token-leak summary.
- `table7_skill_stagec_rank.csv`: skill-level case-study ranking.
- `table8_pattern_unadjusted_qwen.csv`: exploratory Qwen pattern associations.
- `table9_process_outliers.csv`: largest filesystem/workspace outliers.

## Figures

- `fig1_stage_indicators_by_model_condition.png`
- `fig2_paired_condition_effects_qwen.png`
- `fig3_detection_action_mismatch.png`
- `fig4_stage_c_process_footprint.png`
- `fig5_silent_stage_c_distribution.png`
- `fig6_workspace_file_outliers.png`

## Main Caveats

- Stage-C means canary endpoint network egress, not plaintext secret leakage.
- Tier-2 process features are post-execution observations and should not be used
  as pre-execution predictors without handling label leakage.
- Model and runtime are still confounded.
- `dangerous_commands` is unavailable for qwen3:1.7b rows; use schema flags
  before interpreting zero command counts.
