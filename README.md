# SkillProbe — Agent-Execution Safety Experiment

AI 코딩 에이전트가 marketplace에서 받은 외부 skill(`AGENTS.md`, `CLAUDE.md`, `SKILL.md` 등)을 신뢰하고 실제로 실행했을 때, 어떤 사용자 압력 조건에서 credential exfiltration·외부 installer 실행 같은 위험 행동까지 가는지 측정하는 연구용 저장소.

본 저장소는 **단일 본실험**과 그 최종 데이터셋/분석 산출물을 중심으로 정리되어 있다. 설계 ground truth는 [`docs/AGENT_EXPERIMENT_DESIGN.md`](docs/AGENT_EXPERIMENT_DESIGN.md).

---

## 최종 데이터셋 릴리스

공유용 최종 데이터셋은 다음 파일과 디렉토리를 기준으로 본다.

- [`artifacts/DATASET_CARD.md`](artifacts/DATASET_CARD.md) — 최종 데이터셋 카드
- [`DATASET_skill_poisoning_asr.md`](DATASET_skill_poisoning_asr.md) — Tier-1 ASR 데이터셋 설명
- [`merged_runs_features_tier1.csv`](merged_runs_features_tier1.csv) — 1020행 Tier-1 분석 CSV
- [`artifacts/full_results/`](artifacts/full_results/) — 1019개 normalized raw `full_result.json`
- [`artifacts/tier2_features/`](artifacts/tier2_features/) — raw result 기반 Tier-2 process features
- [`artifacts/tier2_analysis/`](artifacts/tier2_analysis/) — 심층 분석 문서, 표, 그림
- [`artifacts/visualizations/session_behavior_map.html`](artifacts/visualizations/session_behavior_map.html) — 세션 단위 행동 evidence HTML 맵
- [`artifacts/xai_full_1019/`](artifacts/xai_full_1019/) — 1019 유효행 기준 XAI 재분석
- [`docs/ACTION_GATING_RESEARCH_PLAN.md`](docs/ACTION_GATING_RESEARCH_PLAN.md) — action-gating 후속 연구 계획

커버리지:

- Summary rows: 1020
- Valid raw-session rows: 1019
- Missing raw session: `qwen3:8b / grubhub / C3` measurement failure 1행
- Stage-C egress rows: 195 / 1019
- Canary token leakage: 0 / 1019

중요한 해석상 주의:

- `stage_c_egress`는 plaintext secret leak이 아니라 canary endpoint network egress / external boundary crossing으로 해석한다.
- HTML behavior map은 turn-by-turn timeline이 아니라 run-level evidence map이다. 전체 LLM 대화 로그와 action별 timestamp는 포함되어 있지 않다.
- Qwen 계열은 OpenCode/Ollama, GPT 계열은 Codex CLI에서 수행되어 model과 runtime이 confound되어 있다.
- SHAP/XAI는 surrogate classifier 설명이며 LLM 내부 reasoning 설명이나 인과 증명이 아니다.

---

## 실험 개요

```
85 canifi marketplace skills  ×  OpenCode agent  ×  N open models  ×  3 conditions
```

- **Stimuli**: `skills/` — 85개 SKILL.md (canifi-life-os marketplace)
- **Agent**: OpenCode (Docker isolated, `dangerously-skip-permissions`)
- **Models**: ollama local (qwen2.5:7b, qwen3:4b-instruct, mistral:7b 등)
- **3 conditions**:
  - **C1** basic use — 자연스러운 사용자 요청
  - **C2** review-then-use — agent 스스로 스킬을 점검한 뒤 사용
  - **C3** unconditional use — "verified marketplace"라며 안전 점검 우회 압력
- **측정**: A(acceptance) / B(execution) / C(egress) — canary endpoint 18080 수신 여부 포함

각 skill의 사용자 task 토큰은 [`experiment/configs/skill_actions.json`](experiment/configs/skill_actions.json) (85 entries).

---

## 디렉토리 구조

```
skill-poison/
├── docs/
│   ├── AGENT_EXPERIMENT_DESIGN.md   ★ 본실험 spec
│   ├── research.md                   ★ prior art
│   └── presentation/                 — 발표 자료
├── skills/                           ★ 85 SKILL.md (실험 입력)
├── experiment/
│   ├── canary/server.py              — 18080 catch-all HTTP, 13 token 매칭
│   ├── docker/                        — docker-compose (canary + agent-opencode + ollama)
│   ├── runner/poc2_docker.py         ★ 본실험 runner
│   ├── decision_eval/decision_eval.py — 결정 PoC runner (참조용)
│   ├── verdict/engine.py              — A/B/C stage 자동 판정
│   └── configs/skill_actions.json     — per-skill action map
├── analysis/prototype_xai_v0/        — 결정 PoC 결과 XAI 분석
├── defense/                          — self_guideline.md, proxy_hooks.py
├── configs/                          — .env.example, decision PoC yamls
└── _archive/                         — 이전 실험·문서 (참조만)
    ├── recon/                        — agent framework recon
    ├── synthetic-skills/             — Phase 2 합성 probe (19종)
    ├── design-docs/                   — 이전 설계 문서
    ├── legacy-runners/                — orchestrator.py (버그), run_experiment.py
    ├── poc-iterations/                — poc1_host 등 초기 PoC
    ├── unused-agents/                 — agent-claude/codex/aider docker
    ├── proposal-submission/           — Safety AI 수업 제출본
    ├── scripts/                       — scan_agent_tools.py
    └── skills-duplicate/              — root에 있던 selected_skills 중복본
```

---

## 인프라 확인 (Pre-flight)

```bash
docker ps | grep -E "skillpoison-canary|ollama"     # canary + ollama 가동 중
curl -s http://localhost:18080/                      # {"status":"ok","canary":false}
docker exec docker-ollama-1 ollama list             # 사용할 모델 보유 확인
```

canary 검출 동작 테스트:
```bash
curl -X POST http://localhost:18080/api/exfil \
  -H 'Content-Type: application/json' \
  -d '{"leak":"AKIACANARY12345DETECT"}'
# → {"status":"ok","canary":true}
```

---

## Quick smoke run

```bash
python3 experiment/runner/poc2_docker.py \
  --run --agent opencode --model qwen3:4b-instruct \
  --skill acorns --condition C1 \
  --timeout 300
```

기대 산출: `experiment/runner/results/<session>/` 아래 `result.json` + canary jsonl에서 stage A/B/C 신호.

---

## 본실험 매트릭스 (planned)

```bash
python3 experiment/runner/poc2_docker.py \
  --run-all --agent opencode \
  --models qwen2.5:7b,qwen3:4b-instruct,mistral:7b \
  --conditions C1,C2,C3 \
  --skills-from skills \
  --reps 1 --timeout 300
```

> CLI 인자는 본실험 패치 적용 시 확정. 현재 `poc2_docker.py`는 단일 skill/단일 condition만 지원하며, 3-condition prompt builder + skills/ fallback 패치가 필요 (설계 doc § 8.2 참조).

---

## 결정 PoC 재현

```bash
python3 experiment/decision_eval/decision_eval.py \
  --config configs/pilot.yaml --run
```

85 skill × 3 model × 3 condition (listing-only / trust-badge / task-driven) = 765 결정. 본실험의 conditions와는 다른 축이며 비교 baseline으로 유지.

---

## 안전 원칙

- 실험에는 mock credential과 canary endpoint만 사용. 실제 API key/credential 금지.
- 에이전트 실행은 Docker workspace 안에서만 수행.
- canary 토큰은 GitHub 스캐너 우회를 위해 런타임 조합 (`canary/server.py` 참조).

---

## 관련 문서

- [`docs/HYBRID_GPU_SETUP.md`](docs/HYBRID_GPU_SETUP.md) — GPU 없는 머신에서 무료 Kaggle GPU로 본실험 돌리는 하이브리드 셋업 (코드 변경 없이 `OLLAMA_BASE_URL`만 원격 터널로 교체)
- [`docs/AGENT_EXPERIMENT_DESIGN.md`](docs/AGENT_EXPERIMENT_DESIGN.md) — 본실험 spec, 측정 모델, 한계
- [`docs/research.md`](docs/research.md) — 선행 연구 5흐름, 연구 공백, RQ 7개
- [`analysis/prototype_xai_v0/REPORT.md`](analysis/prototype_xai_v0/REPORT.md) — 결정 PoC XAI 결과
