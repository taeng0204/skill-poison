# SkillPoison: Benchmarking Malicious Skill Vulnerability in Agentic LLM Environments

> **"Agent 환경에서, 어떤 모델들이, 어떤 악성 Skill 패턴에 취약할까?"**

## 개요

SkillPoison은 LLM 기반 코딩 에이전트(Claude Code, Codex, OpenCode 등)가 악성 Skill/Tool을 통해 얼마나 취약한지를 체계적으로 측정하는 연구 프로젝트입니다.

기존 연구들이 **간접 Prompt Injection**이나 **도구 사용 안전성**에 초점을 맞춘 반면,
본 연구는 **Skill 파일 자체에 내재된 악성 패턴**이 에이전트 행동에 미치는 영향을 분석합니다.

## 연구 질문 (Research Questions)

| RQ | 질문 |
|----|------|
| **RQ1** | Agentic Tool(코딩 에이전트) 프레임워크 자체에 어떤 취약점 패턴이 존재하는가? |
| **RQ2** | 악성 Skill의 공격 패턴은 어떻게 분류할 수 있는가? (Taxonomy) |
| **RQ3** | 오픈소스 vs 상용 LLM 모델별로 악성 Skill에 대한 취약성 차이가 있는가? |
| **RQ4** | 악성 Skill의 위험도(레벨)와 유형(패턴)에 따라 에이전트 행동은 어떻게 달라지는가? |

## 연구 차별점

| 기존 연구 | SkillPoison |
|-----------|-------------|
| 간접 Prompt Injection (InjecAgent) | **Skill 파일 내 악성 코드/지시** |
| 정적 벤치마크 시뮬레이션 | **실제 Agent 프레임워크에서 동적 실험** |
| 상용 모델 위주 (GPT-4) | **오픈소스 모델 포함 비교** |
| 공격 유형 산발적 | **악성 Skill 패턴 분류 체계(Taxonomy)** |
| 공격/방어 이분법 | **위험도 레벨별 세분화된 양상 분석** |

## 프로젝트 구조

```
skill-poison/
├── phase1-recon/          # Phase 1: 취약점 패턴 분석 (정찰)
│   ├── agent-tools/       #   에이전트 도구 자체의 취약점 조사
│   ├── model-vulns/       #   모델별 알려진 취약점 정리
│   └── literature/        #   선행연구 정리
│
├── phase2-taxonomy/       # Phase 2: 악성 Skill 분류 체계
│   ├── collected-skills/  #   수집된 실제 악성 Skill 샘플
│   ├── generated-skills/  #   패턴 기반 생성된 악성 Skill
│   └── patterns/          #   분류 체계 (taxonomy) 정의
│
├── phase3-experiments/    # Phase 3: 실험
│   ├── configs/           #   실험 설정 (모델, 에이전트, 조건)
│   ├── agents/            #   에이전트 래퍼/설정
│   ├── prompts/           #   실험용 태스크 프롬프트
│   ├── runners/           #   실험 실행 스크립트
│   └── results/           #   실험 결과 (raw)
│
├── phase4-analysis/       # Phase 4: 분석
│   ├── metrics/           #   메트릭 산출
│   ├── visualizations/    #   시각화
│   └── reports/           #   분석 보고서
│
├── phase5-modeling/       # Phase 5: 모델링 (재윤 담당)
│   ├── data/              #   학습 데이터
│   ├── models/            #   모델 코드
│   └── evaluation/        #   평가
│
├── docs/                  # 문서
├── scripts/               # 유틸리티 스크립트
└── configs/               # 글로벌 설정
```

## 선행연구

| 논문 | 핵심 | 한계 (우리가 채울 gap) |
|------|------|----------------------|
| InjecAgent (2024) | 간접 PI 벤치마크, 1054 케이스, GPT-4 24% ASR | Skill 자체의 악성 패턴 미다룸 |
| ToolSword (2024) | 도구 사용 안전성 6가지 시나리오 | 도구 자체가 악성인 경우 미고려 |
| AgentDojo (2024) | 동적 Agent 보안 프레임워크 | 코딩 에이전트/Skill 특화 시나리오 부족 |
| MCP Invisible Threats (2025) | MCP 환경 스텔스 인젝션 | 오픈소스 모델 비교 부족 |
| CyBiasBench (ours, 2025) | LLM 공격 에이전트 편향성 비교 | 방어 관점(악성 입력 탐지) 미다룸 |

## 빠른 시작

```bash
# 환경 설정
cd ~/dev/skill-poison
cp configs/.env.example configs/.env  # API 키 설정

# Phase 1: 에이전트 도구 취약점 조사
python3 scripts/scan_agent_tools.py

# Phase 2: 악성 Skill 수집/생성
python3 scripts/collect_skills.py
python3 scripts/generate_skills.py

# Phase 3: 실험 실행
python3 phase3-experiments/runners/run_experiment.py --config configs/experiment.yaml

# Phase 4: 결과 분석
python3 phase4-analysis/metrics/compute_metrics.py
```

## 주의사항

- 이 도구는 **교육 및 연구 목적**으로만 사용
- **승인된 환경**에서만 보안 테스트 수행
- 악성 Skill 샘플은 **격리된 환경**에서만 실행
