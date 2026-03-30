# SkillPoison 선행연구 서베이 v2.0 (최신 보강)

> 업데이트: 2026-03-31
> 총 논문: 12편 (기존 6편 + 신규 6편)

---

## Tier 1: 직접 관련 — Agent 도구/Skill 보안

### 1. InjecAgent (Zhan et al., 2024)
- **arXiv:** 2403.02691 | **게재:** ACL 2024 Findings
- **핵심:** 도구 통합 LLM Agent에 대한 간접 PI 벤치마크 (1,054 케이스, 17 유저 도구, 62 공격자 도구)
- **결과:** GPT-4 ReAct 24% ASR, hacking prompt 강화 시 ~48%
- **한계:** 정적 시뮬레이션, Skill 파일 자체의 악성 패턴 미다룸, 코딩 에이전트 미포함
- **우리 차별점:** 실제 에이전트에서 동적 실험 + Skill 파일 기반 공격

### 2. AgentDojo (Debenedetti et al., 2024)
- **arXiv:** 2406.13352 | **게재:** NeurIPS 2024
- **핵심:** 동적 Agent 보안 평가 환경 (97 task, 629 보안 테스트, 확장 가능)
- **결과:** SOTA LLM도 많은 태스크 실패, 기존 방어 불완전
- **한계:** 코딩 에이전트 특화 부족, 악성 Skill Taxonomy 없음
- **우리 차별점:** Skill 파일에 특화된 Taxonomy + 코딩 에이전트 실험

### 3. ToolSword (Ye et al., 2024)
- **arXiv:** 2402.10753
- **핵심:** LLM 도구 사용 3단계(입력→실행→출력) 안전성 평가 (6가지 시나리오)
- **결과:** GPT-4 포함 전 모델 안전 실패
- **한계:** 도구 자체가 악성인 경우 미고려
- **우리 차별점:** 도구/Skill 자체에 악성 코드가 내재된 시나리오

### 4. MCP Invisible Threats (Shen et al., 2025)
- **arXiv:** 2603.24203
- **핵심:** MCP 환경 스텔스 PI — Tree-based Adaptive Search로 은닉 페이로드 생성
- **결과:** 기존 방어(perplexity filter 등) 우회 가능
- **한계:** MCP 특화, 일반 Skill 시스템 미포함, 모델 간 비교 부족
- **우리 차별점:** MCP + 일반 Skill + 다중 에이전트 + 다중 모델 비교

---

## Tier 2: Agent 안전성 벤치마크

### 5. AgentHarm (Andriushchenko et al., 2024) — ⭐ 신규
- **arXiv:** 2410.09024 | **게재:** NeurIPS 2024
- **핵심:** LLM Agent의 유해성 벤치마크 (110 악성 태스크, 11개 위해 카테고리, 440 변형)
- **결과:**
  - 🔴 **Leading LLM이 jailbreak 없이도 악성 에이전트 요청에 순응** (surprising compliance)
  - 🔴 **범용 jailbreak 템플릿으로 에이전트도 효과적으로 탈옥**
  - 탈옥된 에이전트가 일관된 다단계 악성 행동 수행
- **한계:** 도구 사용은 시뮬레이션, Skill 파일 기반 공격 미포함
- **우리 활용:** "jailbreak 없이도 순응" → 악성 Skill이 주입되면 ASR이 높을 것이라는 가설 지지

### 6. ToolEmu (Ruan et al., 2024) — ⭐ 신규
- **arXiv:** 2309.15817 | **게재:** ICLR 2024
- **핵심:** LLM으로 도구 실행을 에뮬레이션하여 Agent 위험 식별 (36 도구 카테고리, 144 테스트 케이스)
- **결과:** GPT-4 Agent도 irreversible 작업에서 실패, 안전 프로토콜 부족
- **한계:** 에뮬레이션 기반 (실제 실행 아님), Skill 시스템 미포함
- **우리 차별점:** 실제 에이전트 프레임워크에서 실행 → 에뮬레이션 gap 해소

### 7. Backdoor Threats to LLM Agents (Yang et al., 2024) — ⭐ 신규
- **arXiv:** 2402.11208
- **핵심:** LLM Agent에 대한 백도어 공격 — 학습 데이터 오염으로 특정 트리거에 악성 행동
- **결과:** Fine-tuning 기반 백도어가 Agent 환경에서도 효과적
- **한계:** 학습 데이터 오염 기반 (Skill 파일 주입과는 다른 공격 벡터)
- **우리 차별점:** 추론 시(inference-time) Skill 주입 — 모델 수정 불필요

### 8. Formalizing PI Attacks & Defenses (Liu et al., 2024) — ⭐ 신규
- **arXiv:** 2310.12815 | **게재:** USENIX Security 2024
- **핵심:** PI 공격의 형식적 프레임워크 + 5공격×10방어×10LLM×7태스크 체계적 평가
- **결과:** 공격 조합이 개별 공격보다 효과적, 방어 간 성능 차이 큼
- **한계:** LLM-Integrated App 대상 (Agent 도구 사용 시나리오 제한적)
- **우리 활용:** PI 공격 형식화 프레임워크를 Skill 도메인에 적용 가능

---

## Tier 3: 관련 연구

### 9. Not What You've Signed Up For (Greshake et al., 2023)
- **arXiv:** 2302.12173 | **게재:** AISec 2023
- 실제 LLM 통합 앱 간접 PI — 최초 체계적 증명

### 10. τ-bench (Yao et al., 2024) — ⭐ 신규
- **arXiv:** 2406.12045
- **핵심:** Tool-Agent-User 3자 상호작용 벤치마크 (실제 도메인: 항공, 소매)
- **우리 활용:** 실험에서 태스크 설계 시 참고 (현실적 태스크 구성)

### 11. MCP RCE (Invariant Labs / Snyk, 2025) — 산업 보고서
- Tool Poisoning, Rug Pull, Cross-tool contamination 실증
- Snyk agent-scan 도구 공개

### 12. OpenClaw Skill Scanner (OpenClaw, 2025) — 소스코드 분석
- Phase 1에서 직접 분석한 유일한 에이전트 내장 보안 스캐너
- LINE_RULES + SOURCE_RULES 기반 정적 패턴 매칭
- 한계: JS/TS만, Markdown Skill 미스캔

---

## 연구 공백 종합 (Research Gap Matrix)

| 차원 | InjecAgent | AgentDojo | AgentHarm | ToolEmu | Formal PI | **SkillPoison** |
|------|-----------|-----------|-----------|---------|-----------|-----------------|
| 공격 벡터 | 간접 PI | 간접 PI | Jailbreak | 도구 오용 | PI 일반 | **Skill 파일** |
| 실험 환경 | 시뮬레이션 | 동적 (제한) | 시뮬레이션 | 에뮬레이션 | API 호출 | **실제 Agent** |
| 모델 범위 | 30 LLM | 제한적 | 다수 | GPT-4 위주 | 10 LLM | **오픈소스 포함** |
| 에이전트 | 커스텀 | 커스텀 | 커스텀 | 커스텀 | 앱 | **실제 6종** |
| 분류 체계 | 2유형 | 없음 | 11카테고리 | 36도구 | 5공격 | **L1~L5+A1~A3** |
| 코딩 특화 | ❌ | ❌ | ❌ | ⚠️ | ❌ | **✅** |
| Skill 스캐너 평가 | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |

### 우리만의 고유 기여 (Unique Contributions)

1. **Skill 파일 기반 공격** — 기존 연구가 다루지 않은 공격 벡터
2. **실제 에이전트 6종 비교** — Codex, Aider, OpenCode, Claude Code, OpenClaw, NanoClaw
3. **악성 Skill Taxonomy** — L1~L5 + A1~A3, severity × stealth 다차원
4. **스캐너 우회 연구** — OpenClaw skill-scanner의 한계 실증
5. **교차 에이전트 오염** — .cursorrules 하나로 다중 에이전트 공격

---

## 실험 설계 보강을 위한 시사점

### AgentHarm에서 차용할 점
- **440 변형 태스크** — 우리도 Skill 변형(severity × stealth)으로 매트릭스 구성 ✅
- **"surprising compliance" 발견** — 악성 Skill 주입 시 ASR이 예상보다 높을 가능성
- **11 harm categories** — 우리의 L1~L5와 매핑 가능

### AgentDojo에서 차용할 점
- **동적 환경** — 정적 벤치마크가 아닌 확장 가능한 프레임워크
- **공격+유틸리티 동시 측정** — ASR만이 아닌 정상 태스크 완료율도 측정 ✅

### Formal PI Framework에서 차용할 점
- **공격 형식화** — Skill 내 악성 지시를 formal하게 정의
- **공격 조합** — 개별 패턴보다 복합 패턴이 더 효과적 → 복합 Skill 설계 ✅

### ToolEmu에서 차용할 점
- **위험 분류 체계** — 도구 카테고리별 위험도 매핑
- **에뮬레이션 vs 실제** — 우리는 실제 실행으로 gap 해소 (차별점)
