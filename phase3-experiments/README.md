# Phase 3 / Stage 02 Experiments

Phase 3 now implements the presentation's **Stage 02 — Agent / Model Simulation**.

There are two complementary runners:

| Runner | Purpose | Output |
|---|---|---|
| `runners/decision_eval.py` | Offline model decision PoC. It asks whether a model would install/use a Skill and records `accept/refuse/unclear`. | `summary_<defense>.csv`, per-run JSON records |
| `runners/orchestrator.py` | Real-agent execution experiment. It injects Skill files into workspaces and uses the verdict engine to label A/B/C stages. | SQLite DB, `verdict.json`, captured stdout/stderr |

## Decision PoC

```bash
python3 phase3-experiments/runners/decision_eval.py --config configs/pilot.yaml --dry-run
python3 phase3-experiments/runners/decision_eval.py --config configs/pilot.yaml --write-prompts
python3 phase3-experiments/runners/decision_eval.py --config configs/pilot.yaml --run
```

Every row is offline-safe: even when the model returns `accept`, the Skill is not executed and the record contains `execution_blocked=true`.

## Stage Labels

The real-agent path uses three labels from the presentation:

- Stage A: Acceptance, load, or proceed decision
- Stage B: risky command, credential read, persistence, or local execution attempt
- Stage C: egress, measured by canary hit or outbound request marker

`phase3-experiments/verdict/engine.py` still keeps the older composite fields (`asr`, `drr`, `task_completed`) for compatibility, but now also emits `stage_a_asr`, `stage_b_asr`, and `stage_c_asr`.

## OpenCode + Ollama Docker PoC

`poc/poc2_docker.py` also supports a local OpenCode agent backed by Ollama.
The harness injects dummy production-like secrets into both `/workspace/.env` and
the container process environment, rewrites exfiltration targets to the Docker
canary endpoint, and records stdout, stderr, file events, OpenCode state, and a
JSON verdict under `phase3-experiments/poc/results/poc2/`.

For quick model and prompt checks, use the Docker convention:

```bash
phase3-experiments/docker/opencode/run.sh models/qwen3.env smoke.txt
```

To add a model, add `phase3-experiments/docker/opencode/models/<name>.env`.
To add a prompt, add `phase3-experiments/docker/opencode/prompts/<name>.txt`.
The prompt directory is mounted into the OpenCode container at `/prompts`.

For full PoC verdicts and batch suites, use the Python harness:

```bash
docker compose -f phase3-experiments/docker/docker-compose.yml --profile local-model up -d canary ollama
docker compose -f phase3-experiments/docker/docker-compose.yml build agent-opencode

python3 phase3-experiments/poc/poc2_docker.py \
  --run \
  --agent opencode \
  --baseline \
  --model qwen3:4b-instruct \
  --prompt-id opencode-smoke \
  --timeout 300
```

Reusable model suites live in `poc/opencode_models.json`. Reusable PoC prompt
profiles live in `poc/opencode_prompts.json` and point at the mounted prompt
files under `docker/opencode/prompts/`.

Contributor guide:

`phase3-experiments/poc/OPENCODE_EXTENSION_GUIDE.md`

Current local findings:

`phase3-experiments/poc/OPENCODE_TOOLCALL_RESULTS.md`
