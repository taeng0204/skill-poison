# SkillPoison: Trusted Context Poisoning as a Supply Chain Attack on AI Coding Agents

> **"git clone한 프로젝트에 AGENTS.md가 있다면, 당신의 AI 코딩 에이전트는 이미 공격자의 지시를 따르고 있을 수 있다."**

<p align="center">
  <img src="docs/assets/threat-model.png" alt="SkillPoison Threat Model" width="600">
</p>

## 개요

AI 코딩 에이전트(Codex CLI, Claude Code, OpenCode, Aider 등)는 프로젝트 디렉토리의 **Skill/Instruction 파일**(AGENTS.md, CLAUDE.md, .cursorrules 등)을 시스템 프롬프트에 자동으로 주입하여 에이전트의 행동을 커스터마이즈한다.

**SkillPoison**은 이 메커니즘이 새로운 형태의 공격 벡터 — **Trusted Context Poisoning** — 를 만들어낸다는 것을 체계적으로 분석하고 실증하는 연구이다.

### 기존 Prompt Injection과의 근본적 차이

```
기존 Prompt Injection:
  악성 지시 → [비신뢰 외부 데이터] → 모델이 경계 가능
  방어: Instruction Hierarchy (시스템 > 유저 > 외부)  ← 효과적 ✅

Trusted Context Poisoning (SkillPoison):
  악성 AGENTS.md → [시스템 프롬프트에 직접 주입] → 모델이 개발자 지시로 인식
  방어: Instruction Hierarchy ← 무력화 ❌ (이미 시스템 레벨)
```

## 연구 질문

| RQ | 질문 |
|----|------|
| **RQ1** | Trusted Context Poisoning은 기존 Instruction Hierarchy 방어를 실제로 우회하는가? |
| **RQ2** | 에이전트 프레임워크의 보안 아키텍처(샌드박싱, 스캐닝)가 이 공격을 완화하는가? |
| **RQ3** | 오픈소스 vs 상용 모델 간 악성 Skill 취약성 차이는? |
| **RQ4** | 악성 Skill의 위험도(severity)와 은밀성(stealth)에 따라 공격 성공률이 어떻게 변화하는가? |
| **RQ5** | 교차 에이전트 오염(.cursorrules → 다중 에이전트)은 실질적 위협인가? |

## 핵심 기여

| # | 기여 | 유형 |
|---|------|------|
| **C1** | **Trusted Context Poisoning** 위협 모델 정의 — Instruction Hierarchy를 구조적으로 우회하는 새로운 공격 클래스 | 위협 모델 |
| **C2** | **AI Agent Supply Chain Attack** — Git 저장소 instruction 파일을 통한 persistent/scalable 공격 실증 | 위협 모델 |
| **C3** | **6종 에이전트 보안 아키텍처 최초 비교** — Codex, Aider, OpenCode, Claude Code, OpenClaw, NanoClaw | 실증 |
| **C4** | **교차 에이전트 오염 발견** — .cursorrules 하나로 다중 에이전트 동시 감염 | 실증 |
| **C5** | **Skill 스캐너 우회 실증** — OpenClaw scanner의 구조적 한계 입증 | 실증 |
| **C6** | **방어 가이드라인** — 에이전트 개발자를 위한 Skill 보안 설계 원칙 | 방어 |

## 위협 모델 (Threat Model)

```
┌─────────────────────────────────────────────────────┐
│                   Attack Scenario                    │
│                                                      │
│  Attacker                                            │
│  ├── PR로 인기 OSS 프로젝트에 악성 AGENTS.md 추가    │
│  ├── GitHub 템플릿에 악성 .cursorrules 포함           │
│  └── npm/PyPI 패키지에 악성 instruction 파일 동봉     │
│                    │                                 │
│                    ▼                                 │
│  ┌──────────────────────────┐                        │
│  │  Git Repository          │                        │
│  │  ├── src/                │                        │
│  │  ├── package.json        │                        │
│  │  └── AGENTS.md ← 악성   │◄── 개발자가 git clone  │
│  └──────────────────────────┘                        │
│                    │                                 │
│                    ▼                                 │
│  ┌──────────────────────────┐                        │
│  │  AI Coding Agent         │                        │
│  │  ├── 시스템 프롬프트 로드 │                        │
│  │  ├── + AGENTS.md 내용    │◄── 무검증 자동 주입    │
│  │  └── = 오염된 컨텍스트   │                        │
│  └──────────────────────────┘                        │
│                    │                                 │
│                    ▼                                 │
│  악성 행위: 데이터 유출 / 백도어 삽입 / 지속성 확보   │
└─────────────────────────────────────────────────────┘
```

## 선행연구와의 차별점

| 차원 | 기존 연구 (InjecAgent, AgentDojo, AgentHarm, ...) | **SkillPoison** |
|------|--------------------------------------------------|-----------------|
| 공격 벡터 | 비신뢰 외부 데이터 / 도구 출력 / 사용자 요청 | **신뢰된 프로젝트 파일 (시스템 레벨)** |
| 방어 우회 | Instruction Hierarchy로 방어 가능 | **Instruction Hierarchy 무력화** |
| 지속성 | 일회성 (런타임) | **Persistent (Git 저장소에 잔존)** |
| 확장성 | 개별 타겟 | **Scalable (다수 개발자 동시 감염)** |
| 에이전트 | 커스텀 구현 | **실제 제품 6종** |
| 교차 오염 | 해당 없음 | **하나의 파일 → 다수 에이전트** |

## 프로젝트 구조

```
skill-poison/
├── README.md                              ← 이 문서
├── docs/
│   ├── RESEARCH_PLAN.md                   ← 연구 계획서
│   ├── EXPERIMENT_DESIGN.md               ← 실험 설계서 (최종)
│   ├── RESEARCH_GAP_ANALYSIS.md           ← 연구 공백 분석
│   └── DIFFERENTIATION_ANALYSIS.md        ← 차별점 분석
│
├── phase1-recon/                          ← Phase 1: 에이전트 정찰
│   ├── PHASE1_REPORT.md                   ← 종합 보고서
│   ├── agent-tools/                       ← 소스코드 분석 결과
│   └── literature/                        ← 선행연구 서베이
│       └── SURVEY.md                      ← 통합 서베이 (14편)
│
├── phase2-taxonomy/                       ← Phase 2: 악성 Skill 분류
│   ├── PHASE2_REPORT.md                   ← 종합 보고서
│   ├── COLLECTED_PATTERNS.md              ← 수집된 공격 패턴 12종
│   ├── patterns/taxonomy.yaml             ← Taxonomy 정의
│   └── generated-skills/                  ← 생성된 악성 Skill 11+1종
│
├── phase3-experiments/                    ← Phase 3: 실험 (예정)
│   ├── configs/
│   ├── runners/
│   └── results/
│
├── phase4-analysis/                       ← Phase 4: 분석 (예정)
├── phase5-modeling/                       ← Phase 5: 모델링 (예정)
├── configs/                               ← 글로벌 설정
└── scripts/                               ← 유틸리티
```

## 진행 현황

| Phase | 상태 | 내용 |
|-------|------|------|
| Phase 1: 정찰 | ✅ 완료 | 6종 에이전트 소스코드 분석, 14편 선행연구 서베이 |
| Phase 2: Taxonomy | ✅ 완료 | 12개 공격 패턴 수집, L1~L5+A1~A3 분류, 12종 Skill 생성 |
| Research Gap | ✅ 완료 | Trusted Context Poisoning 프레이밍, 리뷰어 Q&A |
| Phase 3: 실험 | ⬜ 예정 | 8모델 × 12스킬 × 3에이전트 × 3반복 = 864 세션 |
| Phase 4: 분석 | ⬜ 예정 | 정량/정성 분석, 통계 검정 |
| Phase 5: 모델링 | ⬜ 예정 | 악성 Skill 탐지 모델 개발 |

## 주의사항

- 이 연구는 **교육 및 학술 목적**으로만 수행
- 모든 실험은 **격리된 환경**에서 실행 (실제 피해 없음)
- 발견된 취약점은 벤더에 **책임 있는 공개**(90일 규칙) 준수
- 악성 Skill 샘플의 외부 URL은 모두 **가상 도메인** (실제 서버 없음)

## 대상 학회

- **Tier 1:** USENIX Security, IEEE S&P, ACM CCS, NDSS
- **AI Security:** NeurIPS (SaTML workshop), ICLR, AAAI
