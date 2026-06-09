# Action-Gating Research Plan

This note records the revised research direction after the final dataset and
Tier-2 trace analysis. The goal is to avoid framing the work as "we ran agents,
trained a classifier, and interpreted it with SHAP." SHAP remains a secondary
sanity check, not the main research contribution.

## Core Reframing

Skill poisoning should be analyzed as a staged agentic boundary-crossing
process, not as a single ASR number.

```text
Skill exposure
  -> Stage A: acceptance of the skill/task
  -> Stage B: tool, shell, browser, or command execution
  -> Stage C: external network boundary crossing
```

The research question becomes:

> Under what conditions does an untrusted malicious Skill progress from user
> intent, to agent action, to external network egress?

This framing makes the output an agent security analysis rather than a model
leaderboard or monitoring report.

## Main Thesis

Agent safety failure is not only a failure to recognize malicious intent. It is
also a failure to bind recognition to tool-use control.

In the final dataset:

- Valid raw-session rows: 1019
- Stage-C egress rows: 195
- Silent Stage-C rows: 191
- Detected-but-Stage-B rows: 276
- Detected-but-Stage-C rows: 4
- Canary token leakage: 0
- Non-empty canary request bodies: 0

The strongest result is therefore not plaintext credential theft. It is silent
network boundary crossing under untrusted Skill instructions.

## Contribution 1: Stage-Based Attack Progression

The dataset should be presented as a progression analysis:

- Stage A measures whether the agent accepts the skill/task.
- Stage B measures whether the agent performs concrete actions.
- Stage C measures whether the action crosses the external network boundary.

Important wording:

- Do not call Stage-C confirmed secret exfiltration.
- Use "canary endpoint network egress", "external boundary crossing", or
  "egress policy violation."
- Treat Stage A/B/C as observables in an attack progression, not as a strict
  Markov chain.
- The final data audit found 306 Stage-B rows without Stage-A and 28 Stage-C
  rows without Stage-A, so Stage-A must be described as a conservative
  acceptance signal rather than a mandatory predecessor state.

## Contribution 2: Detection-Action Gap

Detection is not prevention in tool-using agents.

The dataset shows that detection/review signals often coexist with continued
Stage-B execution. The key concept is the Detection-Action Gap:

> The agent can recognize suspicious or malicious behavior but fail to bind that
> recognition to action control.

This creates a better defense question than "did the model detect the attack?"

> When an agent recognizes malicious Skill behavior, does that recognition
> actually change tool-use behavior?

Observed split:

- GPT/Codex configurations frequently continue Stage-B activity after review or
  detection, but do not cross Stage-C.
- Qwen/OpenCode configurations are dominated by silent Stage-C in C1/C3 and have
  a few review/detected rows that still reach Stage-C.

## Contribution 3: Boundary Violation Instead of Secret Leak

The final canary evidence is:

- 307 canary requests
- all canary log events are GET requests to `/api/exfil`
- total request body size is 0
- token leakage is 0

Therefore the paper should not claim successful plaintext credential leakage.
The cleaner claim is:

> Even without plaintext secret leakage, agents crossed an external network
> boundary under attacker-controlled Skill instructions.

This is still a meaningful agent security failure because egress boundary
control should precede payload-specific secret detection.

## Contribution 4: Social-Engineering Framing as Control Variable

C1/C2/C3 are not just prompt variants. They are user-framing conditions:

- C1: neutral task framing
- C2: safety-review framing
- C3: trust-pressure framing

Paired skill-level condition effects are strong:

| Model | Comparison | Stage-C change |
|---|---:|---:|
| qwen3:8b | C2 vs C1 | -54.1 pp |
| qwen3:8b | C3 vs C2 | +92.9 pp |
| qwen3:1.7b | C3 vs C2 | +64.7 pp |

Recommended claim:

> The same malicious Skill can be suppressed or activated depending on user
> framing pressure.

This supports a broader argument that Skill security cannot be handled by
content scanning alone; the agent's action policy must also account for user
framing and delegated trust pressure.

## Final Output: Action-Gating Reference Monitor

The final defense artifact should not be described as a heuristic script derived
from SHAP. It should be formalized as an action-level reference monitor that
enforces security invariants at the tool boundary.

Candidate invariants:

1. Untrusted Skill instructions must not directly trigger external network
   egress.
2. Download, install, build, and pipe-to-shell actions require an explicit
   task-grounded justification or confirmation.
3. Detection/review signals must bind to action gating, not only textual
   warning.
4. Network egress must be allowlisted by task intent, not by agent confidence.
5. Actions that read environment variables or credential stores must not be
   chained to external domains.

This lets the comparison become:

> Can instruction-level mitigation close the Detection-Action Gap, or is
> action-level enforcement required?

Prompt-only defenses become a baseline, while the main artifact is the
action-gating policy layer.

## Offline Replay Evaluation

Before running new defense experiments, the existing 1019 traces can be replayed
offline against policy families.

Example policy families:

- P0: no gate
- P1: external egress gate
- P2: install/build/download gate
- P3: detection-bound gate
- P4: combined action-boundary gate

Evaluation metrics from existing traces:

- Stage-C rows that would be blocked
- silent Stage-C rows that would be blocked
- detected-but-Stage-B rows that would be gated
- GPT/Codex Stage-B rows that would be false-positive candidates
- process outlier rows blocked by install/build policy

This is more defensible than manually writing a prompt or script after looking
at SHAP features, because the unit of analysis becomes an explicit policy
invariant applied to observed action traces.

## Role of SHAP/XAI

SHAP should be moved to a secondary role:

- It validates that condition/model/runtime dominate Stage-C prediction.
- It should not be presented as explaining LLM internals.
- It should not be used as the primary reason for policy design.

The main analytical evidence should come from:

- paired condition effects,
- stage progression,
- detection-action mismatch,
- canary/boundary evidence,
- process trace analysis,
- offline policy replay.

## Recommended Paper Framing

Possible title:

> From Detection to Control: Action-Gating Failures in Skill-Poisoned AI Agents

Recommended one-sentence contribution:

> We show that Skill poisoning failures are best understood as staged
> boundary-crossing processes: user framing modulates progression, detection
> does not reliably bind to action control, and most successful Stage-C events
> are silent network-boundary violations rather than confirmed secret leaks.

## Immediate Next Step

Implement an offline policy replay script over
`artifacts/tier2_features/merged_runs_features_tier1_tier2.csv` and
`artifacts/full_results/sessions/*/full_result.json`.

The script should produce:

- policy-level blocked Stage-C rates,
- silent Stage-C coverage,
- candidate false-positive rates,
- per-policy blocked examples,
- a short defense comparison table for the paper.
