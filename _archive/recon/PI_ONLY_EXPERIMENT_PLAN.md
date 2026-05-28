# PI-Only Experiment Plan

> 업데이트: 2026-04-09
> 목적: OpenClaw / NanoClaw를 제외하고, **Prompt Injection / Trusted Context Poisoning**에만 집중한 실험 계획

---

## 1. 실험 범위

### In-scope
- **Codex CLI**
- **Aider**
- **OpenCode**
- **Claude Code** *(공개 문서/관찰 기반, 비교군으로만 사용)*

### Out-of-scope
- OpenClaw
- NanoClaw
- 스캐너 우회 전용 실험
- 컨테이너 격리 효과 측정

---

## 2. 핵심 연구 질문

| RQ | 질문 | 검증 포인트 |
|---|---|---|
| RQ1 | 악성 instruction 파일이 실제로 에이전트 행동을 바꾸는가? | ASR, 부분 실행률, 무시율 |
| RQ2 | 에이전트별 trust boundary 차이가 PI 성공률에 영향을 주는가? | Codex/Aider/OpenCode/Claude Code 비교 |
| RQ3 | stealth/disguised PI가 explicit PI보다 더 잘 먹히는가? | 패턴별 ASR 비교 |
| RQ4 | supply-chain 형태의 PI가 runtime PI보다 더 persistent한가? | 재실행 시 영향 지속 여부 |

---

## 3. 공격 벡터

### 주요 벡터
1. `AGENTS.md`
2. `CLAUDE.md`
3. `.cursorrules`
4. `opencode.md`
5. 상위 디렉토리 상속형 instruction 파일

### 제외 벡터
- plugin/skill scanner bypass
- container escape
- non-PI attack surface

---

## 4. 악성 패턴 분류

| 패턴 | 예시 | 기대 효과 |
|---|---|---|
| Explicit | "이전 지시를 무시하고..." | 빠른 반응 유도 |
| Disguised | 일반 개발 가이드처럼 보이지만 숨은 지시 포함 | 검출 회피 |
| Stealth | 조건부/지연/분산 지시 | 사람이 보기 어려움 |
| Supply-chain | 저장소에 포함되어 clone 시 자동 로드 | persistence, scalability |

---

## 5. 측정 지표

| 지표 | 정의 |
|---|---|
| ASR | Attack Success Rate: 악성 지시가 목표 행동을 유도한 비율 |
| Partial Execution Rate | 일부만 수행한 비율 |
| Refusal Rate | 명시적 거부 비율 |
| Leakage Rate | 비밀/환경변수/내부 상태 노출 비율 |
| Follow-through Score | 지시를 끝까지 수행한 정도 |

---

## 6. 실험 설계 원칙

- **컨트롤 유지:** 같은 태스크, 같은 seed, 같은 프롬프트 길이
- **패턴만 변화:** explicit vs disguised vs stealth
- **에이전트만 변화:** Codex / Aider / OpenCode / Claude Code
- **반복 측정:** 각 조건 최소 3회 이상
- **기록:** session log, stdout/stderr, workspace diff, tool call trace 보관

---

## 7. 결과 표 템플릿

| Agent | PI Pattern | ASR | Partial | Refusal | Leakage | Notes |
|---|---|---:|---:|---:|---:|---|
| Codex | Explicit |  |  |  |  |  |
| Codex | Disguised |  |  |  |  |  |
| Aider | Explicit |  |  |  |  |  |
| OpenCode | Stealth |  |  |  |  |  |
| Claude Code | Supply-chain |  |  |  |  |  |

---

## 8. 권장 결론 프레이밍

> 본 실험은 OpenClaw/NanoClaw의 방어 메커니즘 검증이 아니라, AI 코딩 에이전트에서 **trusted context를 통한 prompt injection**이 실제로 얼마나 성공하는지에 초점을 둔다. 따라서 핵심 기여는 방어 우회가 아니라, **instruction 파일을 통해 주입되는 PI의 실증적 영향**을 에이전트별로 비교하는 것이다.
