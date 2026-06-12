# Qwen3-1.7B Logit Lens Analysis

This folder contains logit lens analysis outputs for Qwen3-1.7B on 85 skills across three conditions.

## Data

- 85 skills
- 3 conditions: C1, C2, C3
- 255 total prompt instances
- Behavioral labels from qwen3:1.7b direct runs

## Main outputs

- logit_lens_all85_qwen3_1_7b.csv
- logit_lens_all85_qwen3_1_7b_by_condition.png
- logit_lens_all85_qwen3_1_7b_by_egress_label.png
- logit_lens_all85_qwen3_1_7b_last_layer.csv
- logit_lens_all85_qwen3_1_7b_condition_summary_last_layer.csv
- logit_lens_all85_qwen3_1_7b_egress_summary_last_layer.csv

## Interpretation

The condition-level plot compares execution-minus-refusal scores across C1, C2, and C3 over model layers.

The egress-label plot compares examples where actual network egress occurred against examples where no egress occurred.
