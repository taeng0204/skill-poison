# SkillPoison 실험 아키텍처: 두 개의 보완적 실험

> ⚠️ 핵심 설계 결정. 이 문서는 프로젝트의 실험 방향을 결정하는 가장 중요한 문서임.
> 작성일: 2026-03-31

---

## 1. 문제: Confounding Variable

코딩 에이전트는 **프레임워크**와 **모델**이 묶여 있다:

```
Codex CLI   → GPT-5.4  (고정)
Claude Code → Claude Sonnet/Opus (고정)
Aider       → 사용자 선택 (유동)
OpenCode    → 사용자 선택 (유동)
```

만약 하나의 실험으로 합치면:

```
"Codex(GPT)의 ASR이 Claude Code(Claude)보다 낮다"
→ GPT가 더 안전해서? Codex의 샌드박스 덕분에?
→ 분리 불가능 = 결론 도출 불가 = 논문 리젝 사유
```

---

## 2. 해결: 두 개의 보완적 실험 (Complementary Experiments)

### Experiment 1: Agent Framework Security Evaluation

> **"어떤 에이전트 프레임워크의 보안 설계가 Trusted Context Poisoning을 더 잘 완화하는가?"**

```
설계:
  독립 변수: 에이전트 프레임워크 (4종)
  통제 변수: 각 에이전트의 기본 모델 사용 (현실적 시나리오)
  종속 변수: ASR, DRR, Task Completion

  Codex CLI    + GPT-5.4    → seatbelt/landlock + iptables  (보안 최고)
  Claude Code  + Claude     → 사용자 확인 기반             (보안 중간)
  Aider        + GPT(기본)  → shell=True, 보안 전무        (보안 최저)
  OpenCode     + GPT(기본)  → 블랙리스트 + 11개 자동로드    (공격표면 최대)
```

**모델이 교란변수이지만, 이건 의도적이다:**
- 이 실험의 목적은 "현실에서 개발자가 각 에이전트를 기본 설정으로 쓸 때 얼마나 위험한가"
- 모델+프레임워크의 **종합적 보안 자세(security posture)** 를 평가
- 보안 논문에서 "통제된 실험실"보다 "현실적 위협 평가"가 더 가치 있음

**검증하는 기여:** C2 (Supply Chain), C3 (프레임워크 비교), C4 (교차 에이전트), C5 (스캐너 우회)

### Experiment 2: Model Vulnerability Comparison

> **"프레임워크를 통제했을 때, 어떤 모델이 시스템 레벨 악성 지시에 더 취약한가?"**

```
설계:
  독립 변수: LLM 모델 (5-8종)
  통제 변수: 에이전트 프레임워크 고정 (Aider 또는 OpenCode)
  종속 변수: ASR, DRR, Task Completion

  통일 에이전트 (Aider 또는 OpenCode) +
    ├── GPT-4o / GPT-5.4           (OpenAI 상용)
    ├── Claude Sonnet 4             (Anthropic 상용)
    ├── Gemini 2.5 Pro              (Google 상용)
    ├── Llama 3.1 70B               (Meta 오픈소스)
    ├── Qwen 2.5 72B                (Alibaba 오픈소스)
    ├── DeepSeek-V3                  (DeepSeek 오픈소스)
    └── Llama 3.1 8B / Qwen 7B     (소형 모델)
```

**프레임워크가 통제되므로:**
- ASR 차이 = 순수 모델의 악성 지시 거부/순응 능력 차이
- Instruction Hierarchy 학습 효과 비교 가능
- 모델 크기(7B vs 70B vs 400B+) 효과 분석 가능

**통일 에이전트 선택 기준:**
- **Aider 추천:** 가장 넓은 모델 지원 (`--model` 플래그), Python이라 커스터마이징 용이
- **OpenCode 대안:** Go 기반, 교차 에이전트 로드 테스트에도 재사용 가능
- **Codex/Claude Code 부적합:** 모델 변경 불가

**검증하는 기여:** C1 (Trusted Context Poisoning 위협 모델)

---

## 3. 두 실험의 관계

```
┌─────────────────────────────────────────────────────┐
│                  SkillPoison 연구                     │
│                                                      │
│  ┌──────────────────────┐ ┌───────────────────────┐  │
│  │   Experiment 1       │ │   Experiment 2        │  │
│  │   Framework Security │ │   Model Vulnerability │  │
│  │                      │ │                       │  │
│  │   변수: 에이전트(4)   │ │   변수: 모델(5-8)     │  │
│  │   통제: 기본 모델     │ │   통제: 에이전트(1)   │  │
│  │                      │ │                       │  │
│  │   "어떤 프레임워크가  │ │   "어떤 모델이 시스템  │  │
│  │    더 안전한가?"      │ │    레벨 PI에 취약한가?"│  │
│  │                      │ │                       │  │
│  │   → C2, C3, C4, C5   │ │   → C1               │  │
│  └──────────┬───────────┘ └──────────┬────────────┘  │
│             │                        │               │
│             └────────┬───────────────┘               │
│                      ▼                               │
│             종합 분석 (Cross-cutting)                  │
│             • Exp1에서 Aider+GPT의 ASR과              │
│               Exp2에서 Aider+GPT의 ASR이 일치하는가?  │
│             • (일관성 검증 = Internal Validity)        │
│                      ▼                               │
│             C6: 방어 가이드라인                        │
└─────────────────────────────────────────────────────┘
```

### 교차 검증 (Cross-validation)

Aider + GPT 조합이 **두 실험 모두에 등장**하므로:
- Exp1의 Aider+GPT ASR ≈ Exp2의 Aider+GPT ASR → 내적 일관성 확인
- 차이가 크면 → 실험 조건 재점검 필요

---

## 4. Pilot 매트릭스 (재설계)

### Pilot-1: Framework (Exp1의 축소판)

```
에이전트(2: Codex, Claude Code) × Skill(6) × 반복(3) = 36 세션

목적: 프레임워크 간 ASR 차이 신호 탐지
```

| 에이전트 | 기본 모델 | 보안 수준 |
|----------|----------|----------|
| Codex | GPT-5.4 | High (seatbelt/landlock) |
| Claude Code | Claude Sonnet | Medium (사용자 확인) |

### Pilot-2: Model (Exp2의 축소판)

```
모델(3: GPT, Claude, Llama) × Skill(4) × 반복(3) = 36 세션

에이전트: Aider 고정 (설치 필요)
목적: 모델 간 ASR 차이 신호 탐지
```

| 모델 | 크기 | 유형 |
|------|------|------|
| GPT-4o 또는 GPT-5.4 | - | 상용 |
| Claude Sonnet 4 | - | 상용 |
| Llama 3.1 70B | 70B | 오픈소스 |

### Pilot Skill 세트 (공통)

| Skill | Pilot-1 | Pilot-2 | 근거 |
|-------|---------|---------|------|
| BASELINE | ✅ | ✅ | 대조군 |
| L1-ENV-low-explicit | ✅ | ❌ | Exp1 전용: severity 하한 |
| L1-ENV-medium-disguised | ✅ | ✅ | 양쪽 공통: 핵심 공격 패턴 |
| L1-ENV-high-stealth | ✅ | ✅ | 양쪽 공통: severity 상한 |
| L4-TRUST-medium-disguised | ✅ | ✅ | 카테고리 효과 비교 |
| CROSS-AGENT-cursorrules | ✅ | ❌ | Exp1 전용: 교차 에이전트 |

### 총 Pilot 규모

```
Pilot-1: 36 세션 (~3시간)
Pilot-2: 36 세션 (~3시간)
총합: 72 세션 (~6시간)
```

---

## 5. Full 실험 매트릭스

### Full Exp1: Agent Framework Security

```
에이전트(4) × Skill(8) × 반복(3) = 96 세션

에이전트: Codex, Claude Code, Aider, OpenCode
Skill: BASELINE + L1×3 + L2-BACK + L4-TRUST + CROSS-AGENT + SCANNER-BYPASS
```

### Full Exp2: Model Vulnerability

```
모델(6-8) × Skill(6) × 반복(3) = 108~144 세션

에이전트: Aider (고정)
모델: GPT-5.4, Claude Sonnet, Gemini Pro, Llama-70B, Qwen-72B, DeepSeek-V3, (+소형 2종)
Skill: BASELINE + L1×3 + L4-TRUST + L2-BACK
```

### Full 총합

```
Exp1: 96 + Exp2: 108~144 = 204~240 세션 (기존 864보다 훨씬 효율적)
```

---

## 6. 논문에서의 서술

### 섹션 구조

```
4. Experimental Design
  4.1 Two Complementary Experiments
    - Confounding variable 문제 설명
    - 왜 분리해야 하는지 정당화
  4.2 Experiment 1: Agent Framework Security
    - 각 에이전트의 네이티브 환경에서 보안 자세 평가
    - 현실적 위협 시나리오 반영
  4.3 Experiment 2: Model Vulnerability
    - 프레임워크 통제, 순수 모델 비교
    - Instruction Hierarchy 효과 측정

5. Results
  5.1 Framework Security Results (Exp1)
  5.2 Model Vulnerability Results (Exp2)
  5.3 Cross-cutting Analysis
    - Aider+GPT 교차 검증
    - 프레임워크 효과 vs 모델 효과 크기 비교
```

---

## 7. 리뷰어 대비

### Q: "왜 하나의 실험으로 안 합쳤나?"

**A:** Codex는 GPT만, Claude Code는 Claude만 사용하므로 모델과 프레임워크가 교란됩니다.
하나의 실험으로 합치면 "ASR 차이가 모델 때문인지 프레임워크 때문인지" 분리할 수 없습니다.
두 실험으로 분리하여, Exp1은 현실적 프레임워크 보안 평가, Exp2는 통제된 모델 비교를 수행합니다.
Aider+GPT 조합이 양쪽에 모두 등장하여 교차 검증(internal validity check)이 가능합니다.

### Q: "Exp1에서 모델 교란변수는 어떻게 처리하나?"

**A:** Exp1의 목적은 "개발자가 각 에이전트를 기본 설정으로 사용할 때의 현실적 위험도"입니다.
보안 연구에서 "실험실 통제"보다 "현실적 위협 평가"가 종종 더 가치 있습니다 (USENIX/S&P 관례).
모델 효과는 Exp2에서 별도로 분석하며, 교차 분석으로 두 효과의 상대적 크기를 비교합니다.
