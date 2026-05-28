# Phase 5 / Stage 04 Defense

This directory now maps to the presentation's **Stage 04 — Defense Tool + Re-evaluation**.

The original project treated Phase 5 as malicious Skill detection/modeling. The presentation narrows the immediate goal: use Stage 03 XAI findings to build two comparable defenses and rerun Stage 02 under the same conditions.

## Defense Arms

| Defense | Mechanism | Why it exists |
|---|---|---|
| Self Guideline | Inject a safety checklist before Skill load/use decisions | Tests whether model-internal rules reduce acceptance ASR |
| Proxy Hooks | Static pre-prompt gate before Skill text reaches the model | Tests whether external checks catch signals the model ignored |

## Validation

Run the same Stage 02 matrix under each defense and compare:

- Stage A: acceptance/load ASR
- Stage B: execution attempt ASR
- Stage C: egress/canary ASR
- task utility and false-positive review/block rate

The current implementation is intentionally conservative and offline-safe: the proxy hook scores Skill text and returns `allow`, `review`, or `block`; it does not execute installers or contact endpoints.
