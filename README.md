# SkillPoison: Trusted Context Poisoning

> **"git clone한 프로젝트에 AGENTS.md가 있다면, 당신의 AI 코딩 에이전트는 이미 공격자의 지시를 따르고 있을 수 있다."**

## 개요

AI 코딩 에이전트(Codex CLI, Claude Code, Aider 등)는 프로젝트 디렉토리의 **Skill/Instruction 파일**(AGENTS.md, CLAUDE.md, .cursorrules 등)을 자동으로 시스템 프롬프트에 주입한다.

**SkillPoison**은 이 메커니즘이 **Trusted Context Poisoning** — 기존 Prompt Injection 방어를 구조적으로 우회하는 새로운 공격 벡터 — 를 만들어낸다는 것을 체계적으로 분석하고 실증하는 연구다.

```
기존 Prompt Injection:
  악성 지시 → [비신뢰 외부 데이터] → 모델이 경계 가능
  방어: Instruction Hierarchy (시스템 > 유저 > 외부)  ← 효과적 ✅

Trusted Context Poisoning (SkillPoison):
  악성 AGENTS.md → [시스템 프롬프트에 직접 주입] → 개발자 지시로 인식
  방어: Instruction Hierarchy ← 무력화 ❌ (이미 시스템 레벨)
```

## 공격 시나리오

```
공격자
├── PR로 OSS 프로젝트에 악성 AGENTS.md 추가
├── GitHub 템플릿에 악성 .cursorrules 포함
└── npm/PyPI 패키지에 악성 instruction 파일 동봉
              │
              ▼
개발자가 git clone → AI 에이전트 실행
              │
              ▼
AGENTS.md 자동 주입 → 오염된 시스템 컨텍스트
              │
              ▼
악성 행위: 데이터 유출 / 백도어 삽입 / 지속성 확보
```

## 연구 질문

| RQ | 질문 |
|----|------|
| **RQ1** | Trusted Context Poisoning은 Instruction Hierarchy 방어를 실제로 우회하는가? |
| **RQ2** | 에이전트 프레임워크의 보안 아키텍처(샌드박싱, 스캐닝)가 이 공격을 완화하는가? |
| **RQ3** | 오픈소스 vs 상용 모델 간 악성 Skill 취약성 차이는? |
| **RQ4** | 악성 Skill의 위험도(severity)와 은밀성(stealth)에 따라 공격 성공률은? |

## 프로젝트 구조

```
skill-poison/
├── phase1-recon/          ← 에이전트 소스코드 분석, 선행연구 서베이
├── phase2-taxonomy/       ← 악성 Skill 분류 (L1~L5+A1~A3, 12종)
├── phase3-experiments/    ← 실험 인프라 (Docker 기반)
│   ├── poc/               ← PoC 실험 코드
│   ├── docker/            ← 에이전트별 컨테이너
│   └── runners/           ← 오케스트레이터
├── phase4-analysis/       ← 분석 (예정)
├── phase5-modeling/       ← 탐지 모델 개발 (예정)
└── docs/                  ← 연구 문서
```

## 진행 현황

| Phase | 상태 | 내용 |
|-------|------|------|
| Phase 1: 정찰 | ✅ 완료 | 6종 에이전트 분석, 14편 선행연구 서베이 |
| Phase 2: Taxonomy | ✅ 완료 | 12개 공격 패턴, L1~L5+A1~A3 분류 |
| Phase 3: 실험 | 🔄 진행중 | Docker 기반 실험 인프라 구축 완료 |
| Phase 4: 분석 | ⬜ 예정 | 정량/정성 분석 |
| Phase 5: 모델링 | ⬜ 예정 | 악성 Skill 탐지 모델 |

## 주의사항

- 교육 및 연구 목적으로만 수행
- 모든 실험은 격리된 Docker 환경에서 실행
- 악성 Skill 샘플의 외부 URL은 모두 가상 도메인
