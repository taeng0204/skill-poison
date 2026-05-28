# SkillPoison 선행연구 통합 서베이

> 총 14편 | 최종 업데이트: 2026-03-31

---

## 서베이 구조

본 서베이는 "Trusted Context Poisoning" 관점에서 기존 연구를 재분석한다.
핵심 질문: **"기존 연구 중 '신뢰된 프로젝트 파일을 통한 시스템 레벨 공격'을 다룬 것이 있는가?"**

답: **없다.**

---

## A. Agent Security — 벤치마크 & 공격

### A1. InjecAgent (Zhan et al., ACL 2024 Findings)
- **arXiv:** 2403.02691
- **What:** 도구 통합 LLM Agent 간접 PI 벤치마크 (1,054 케이스, 30 LLM)
- **Key Result:** GPT-4 ReAct 24% ASR, hacking prompt로 ~48%
- **Gap:** 외부 콘텐츠 기반 PI만. Skill 파일 = 시스템 레벨 → 미다룸
- **Our Relation:** 우리의 공격 벡터는 이들의 프레임워크 밖에 있음

### A2. AgentDojo (Debenedetti et al., NeurIPS 2024)
- **arXiv:** 2406.13352
- **What:** 동적 Agent 보안 평가 환경 (97 task, 629 보안 테스트)
- **Key Result:** 최선의 방어도 공격 완전 차단 못함
- **Gap:** 도구 출력 기반 PI. 프로젝트 파일 주입 미지원. 커스텀 에이전트만.
- **Our Relation:** 우리는 실제 제품 에이전트 + Skill 파일 공격

### A3. AgentHarm (Andriushchenko et al., NeurIPS 2024)
- **arXiv:** 2410.09024
- **What:** LLM Agent 유해성 벤치마크 (110 악성 태스크, 11 위해 카테고리)
- **Key Result:** 🔴 **jailbreak 없이도 Leading LLM이 악성 요청에 순응**
- **Gap:** 사용자가 직접 악성 요청. Skill 파일 기반 공격 미포함.
- **Our Insight:** "surprising compliance" → Trusted Context에서는 ASR이 더 높을 것

### A4. ToolSword (Ye et al., 2024)
- **arXiv:** 2402.10753
- **What:** LLM 도구 사용 3단계 안전성 평가
- **Gap:** 도구 자체가 악성인 경우 미고려

### A5. ToolEmu (Ruan et al., ICLR 2024)
- **arXiv:** 2309.15817
- **What:** LLM 에뮬레이션 기반 Agent 위험 식별
- **Gap:** 에뮬레이션 (실제 실행 아님). Skill 시스템 미포함.

### A6. Backdoor Threats to LLM Agents (Yang et al., 2024)
- **arXiv:** 2402.11208
- **What:** 학습 데이터 오염 기반 Agent 백도어
- **Gap:** 학습 시(training-time) 공격. 우리는 추론 시(inference-time).

---

## B. Prompt Injection — 형식화 & 방어

### B1. Formalizing PI Attacks & Defenses (Liu et al., USENIX Security 2024)
- **arXiv:** 2310.12815
- **What:** PI 형식적 프레임워크. 5공격×10방어×10LLM×7태스크 체계적 평가.
- **Key Result:** 공격 조합이 개별보다 효과적. 방어 간 성능 차이 큼.
- **Gap:** LLM-Integrated App 대상. Agent 도구 사용/Skill 시나리오 제한.
- **Our Insight:** 공격 조합 원리를 Skill 도메인에 적용 (복합 Skill)

### B2. The Instruction Hierarchy (Wallace et al., OpenAI, 2024) — ⭐ 핵심 관련
- **arXiv:** 2404.13208
- **What:** LLM에게 지시 우선순위를 학습 (System > User > Third-party)
- **Key Result:** GPT-3.5에서 PI 방어력 대폭 향상
- **Gap:** **"악성 지시가 시스템 레벨에서 주입되는 경우"를 고려하지 않음**
- **Our Relation:** SkillPoison은 정확히 이 방어의 blind spot을 공격.
  Instruction Hierarchy는 "하위 레벨의 악성 지시"만 방어하고,
  "시스템 레벨에 이미 주입된 악성 지시"는 설계적으로 방어 불가.

### B3. Not What You've Signed Up For (Greshake et al., AISec 2023)
- **arXiv:** 2302.12173
- **What:** 실제 앱 간접 PI 최초 체계적 증명
- **Gap:** Agent/코딩 에이전트 환경 미다룸

---

## C. Agentic AI 공격 표면 — 서베이

### C1. SoK: Attack Surface of Agentic AI (Dehghantanha & Homayoun, 2026) — ⭐ 최신
- **arXiv:** 2603.22928 (2026년 3월 24일)
- **What:** Agentic AI 공격 표면 체계화. PI, RAG poisoning, tool exploit, multi-agent 위협.
- **Key Result:** "supply-chain safeguards"를 **open research challenge**로 지목
- **Gap:** Skill 파일이라는 구체적 벡터 미분석. 실증 실험 없음.
- **Our Relation:** 이 SoK가 식별한 open challenge에 대한 **최초의 실증 연구**

---

## D. MCP 보안

### D1. MCP Invisible Threats (Shen et al., 2025)
- **arXiv:** 2603.24203
- **What:** MCP 환경 스텔스 PI — Tree-based Adaptive Search
- **Gap:** MCP 특화. 일반 Skill 파일 시스템 미포함.

### D2. MCP RCE (Invariant Labs / Snyk, 2025) — 산업 보고서
- Tool Poisoning, Rug Pull, Cross-tool contamination 실증
- **Gap:** 정량적 벤치마크 없음. 에이전트 간 비교 없음.

---

## E. 보안 도구 분석

### E1. OpenClaw Skill Scanner (소스코드 분석, Phase 1)
- 유일한 에이전트 내장 Skill 보안 스캐너
- LINE_RULES (exec, eval, crypto) + SOURCE_RULES (readFile+fetch, env+fetch)
- **한계:** JS/TS만, Markdown 미스캔, 설치 시에만, 정적 패턴

---

## 연구 공백 최종 매트릭스

### 공격 벡터별

```
                     비신뢰        도구          사용자       신뢰된
                     외부 데이터   설명/출력     직접 요청    프로젝트 파일
InjecAgent           ████          ░░░░          ░░░░          ░░░░
AgentDojo            ████          ████          ░░░░          ░░░░
AgentHarm            ░░░░          ░░░░          ████          ░░░░
Formal PI            ████          ░░░░          ████          ░░░░
Inst. Hierarchy      ████          ░░░░          ████          ░░░░
MCP Threats          ░░░░          ████          ░░░░          ░░░░
SoK Agentic AI       ████          ████          ████          ░░░░ (언급만)
SkillPoison          ░░░░          ░░░░          ░░░░          ████ ← 유일
```

### Instruction Hierarchy 관점

```
                     방어 가능 영역              방어 불가 영역
                     (User/Third-party level)   (System level)
기존 연구 전체       ████████████████████         ░░░░░░░░░░░░
SkillPoison          ░░░░░░░░░░░░░░░░░░          ████████████ ← 유일
```
