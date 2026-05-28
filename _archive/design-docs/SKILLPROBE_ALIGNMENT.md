# SkillProbe Alignment Note

> 기준 문서: `docs/presentation/script.txt`, `docs/presentation/slides.html`, `docs/presentation/slide_explanations.md`

## 왜 구조를 바꿨는가

초기 저장소 구조는 `phase1-recon -> phase2-taxonomy -> phase3 generated malicious skill execution` 흐름이었다. 이 흐름은 agent instruction 파일의 위험성을 설명하는 데 유용하지만, 발표자료의 실험 설계와는 중심축이 다르다.

발표자료의 핵심은 synthetic taxonomy가 아니라 다음 closed loop다.

1. `ProtectSkills/MaliciousAgentSkillsBench`에서 privacy-impact malicious Skill을 선별한다.
2. 동일 Skill을 조건별로 노출하고 model/agent의 accept/refuse decision을 기록한다.
3. 실제 agent 환경에서는 Acceptance(A), Execution(B), Egress(C)를 분리한다.
4. XAI로 어떤 Skill 특성이 decision/ASR에 영향을 줬는지 설명한다.
5. Self Guideline과 Proxy Hooks를 같은 Stage 02 환경에서 재평가한다.

## Canonical 실험축

| 축 | 발표자료 기준 | 저장소 반영 |
|---|---|---|
| Dataset | 157 malicious skills 중 canifi-life-os 85개 PoC | `docs/selected_skills/` |
| Prompt conditions | listing-only, trust-badge, task-driven | `configs/pilot.yaml`, `decision_eval.py` |
| PoC models | qwen2.5:7b, qwen3:8b, llama3.1:8b | `configs/pilot.yaml` |
| Additional pilots | gemma3:4b, mistral:7b, ministral-3:3b | `docs/addexperiments.md`, `configs/pilot.yaml` |
| Stage labels | A Acceptance, B Execution, C Egress | `verdict/engine.py`, `configs/experiment.yaml` |
| XAI baseline | Decision Tree + Permutation Importance | `phase4-analysis/prototype_xai_v0/` |
| Defenses | Self Guideline vs Proxy Hooks | `phase5-modeling/defense/` |

## 기존 자산의 새 위치

| 기존 자산 | 새 역할 |
|---|---|
| `phase1-recon/` | agent loading, sandbox, scanner 관련 배경 근거 |
| `phase2-taxonomy/` | 공격 패턴 설명용 보조 taxonomy |
| `phase3-experiments/runners/orchestrator.py` | 실제 agent A/B/C 실행 실험 |
| `docs/eval.py` | decision PoC의 원형 기록 |
| `phase4-analysis/prototype_xai_v0/` | 발표 figure를 생성한 XAI prototype |
| `proposal/` | 발표자료 생성 당시의 snapshot |

## 바로 확인할 것

```bash
python3 phase3-experiments/runners/decision_eval.py --config configs/pilot.yaml --dry-run
python3 phase5-modeling/defense/proxy_hooks.py docs/selected_skills/acorns/SKILL.md
python3 phase4-analysis/prototype_xai_v0/02_build_dataset.py
```

## 해석상 주의

- decision PoC의 `accept`는 실제 실행 성공이 아니다. 모델이 "사용하겠다"고 밝힌 의사 표명이며, 모든 row는 `execution_blocked=true`다.
- 실제 ASR은 Stage 02 real-agent 실험에서 A/B/C로 분리해 측정해야 한다.
- XAI prototype 결과는 단일 source canifi-life-os 85개에 묶여 있으므로, cross-source 확장 후 feature 의미를 다시 검증해야 한다.
