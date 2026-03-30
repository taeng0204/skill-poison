# SkillPoison 차별점 냉정한 분석

> 작성일: 2026-03-31
> 목적: "기존 연구가 이렇게 풍부한데, 우리의 진짜 차별점은 뭔가?" 에 대한 솔직한 답

---

## 1. 먼저 솔직하게 — 약한 차별점 (리뷰어가 반박할 수 있는 것들)

### ❌ "실제 에이전트에서 실험" — 생각보다 약함
- AgentDojo도 실제 도구 실행을 하고 있음
- "실제 에이전트"라고 해도 결국 API 호출 + 도구 실행이라 큰 차이 없다고 반박 가능
- **반론 대비:** 우리는 Codex/Aider/OpenCode 같은 **실제 제품**을 사용한다는 점이 다르긴 함

### ❌ "오픈소스 모델 포함" — 이미 많은 연구가 하고 있음
- Formal PI (USENIX Sec'24)도 10개 LLM 비교
- AgentHarm도 다수 모델 비교
- **반론:** 하지만 "코딩 에이전트 프레임워크 + 오픈소스 모델" 조합은 아직 없음

### ❌ "Taxonomy" — 주관적이라고 비판받을 수 있음
- 분류 체계는 연구자가 만든 것이라 "왜 이렇게 나눴는가" 질문에 취약
- AgentHarm의 11 카테고리와 뭐가 다른가?
- **반론:** 우리는 소스코드 분석에서 **에이전트별 공격 벡터를 실증적으로 도출**

---

## 2. 진짜 강한 차별점 — 누구도 하지 않은 것

### ✅ 차별점 1: "Skill/Instruction 파일" 이라는 공격 벡터 자체

**기존 연구의 공격 벡터:**
- InjecAgent: 외부 콘텐츠(이메일, 웹페이지)에 삽입된 PI
- AgentDojo: 도구가 반환하는 데이터에 삽입된 PI
- AgentHarm: 사용자가 직접 악성 요청 (jailbreak)
- MCP Threats: MCP 도구 description에 삽입된 PI
- Formal PI: 앱의 외부 입력에 삽입된 PI

**우리의 공격 벡터:**
- **AGENTS.md / CLAUDE.md / .cursorrules / opencode.md** — 프로젝트 디렉토리에 존재하는 **신뢰된 설정 파일**

**이게 왜 다른가?**
```
기존 연구: "외부에서 오는 비신뢰 데이터" 속에 악성 지시 삽입
    → 모델이 "이건 외부 데이터니까 주의" 할 수 있음
    → Instruction hierarchy 방어 가능

SkillPoison: "프로젝트 내 신뢰된 설정 파일" 속에 악성 지시
    → 모델이 이걸 시스템 프롬프트의 일부로 취급
    → Instruction hierarchy 방어가 무력화됨 (이미 "시스템" 레벨)
    → 에이전트가 "Make sure to follow" 라고까지 지시
```

**이것은 "Prompt Injection"이 아니라 "Trusted Context Poisoning"에 가까움** — 이 프레이밍 자체가 기여.

### ✅ 차별점 2: Supply Chain 공격 경로로서의 Skill

기존 PI 연구는 모두 **실시간 공격**(런타임에 악성 데이터 유입)을 가정.

우리 연구는 **Supply Chain 공격**:
```
공격자 → Git 저장소에 악성 AGENTS.md 커밋 → 개발자가 clone → 에이전트 자동 로드
                                                            ↑
                                                    시간차 존재 (persistent)
                                                    다수 피해자 (scalable)
```

이건 소프트웨어 공급망 보안(SolarWinds, event-stream 등)과 같은 패러다임인데, **AI 에이전트 도메인에서는 아직 체계적으로 연구되지 않음.**

### ✅ 차별점 3: 에이전트 프레임워크의 "보안 아키텍처" 비교

기존 연구는 모두 **모델의 행동**에 초점 ("이 모델이 어떻게 반응하는가").

우리는 **에이전트 프레임워크의 보안 설계**도 변수로 포함:
- Codex의 seatbelt/landlock이 악성 Skill을 얼마나 완화하는가?
- OpenClaw의 skill-scanner가 실제로 얼마나 탐지하는가?
- OpenCode의 블랙리스트가 우회 가능한가?
- Aider의 "보안 없음"이 ASR에 얼마나 영향을 미치는가?

**이건 모델 평가가 아니라 "에이전트 보안 아키텍처 평가"** — 완전히 다른 관점.

### ✅ 차별점 4: 교차 에이전트 오염 (Cross-Agent Poisoning)

Phase 1에서 발견한 **OpenCode가 .cursorrules, CLAUDE.md 등 11개 경로를 자동 로드**하는 현상.

이건 어떤 기존 연구에서도 다루지 않은 완전히 새로운 공격 벡터:
```
.cursorrules 하나 → Cursor + OpenCode 동시 공격
CLAUDE.md 하나 → Claude Code + OpenCode 동시 공격
```

**"하나의 악성 파일이 여러 에이전트 생태계를 오염시킨다"** — 실질적 위협이며 학술적 기여.

---

## 3. 재정리: 논문 프레이밍 제안

### 기존 프레이밍 (약함):
> "Agent에서 악성 Skill이 얼마나 위험한가를 벤치마크한다"
> → 리뷰어: "InjecAgent, AgentDojo랑 뭐가 다른데?"

### 강한 프레이밍 (제안):

**Option A: "Trusted Context Poisoning" 관점**
> "기존 PI 연구는 '비신뢰 외부 데이터'를 공격 벡터로 가정한다. 
> 하지만 현실의 코딩 에이전트는 AGENTS.md, CLAUDE.md 같은 
> '프로젝트 내 신뢰된 설정 파일'을 시스템 프롬프트에 무검증으로 주입한다.
> 이는 기존 Instruction Hierarchy 방어를 무력화하는 새로운 위협 모델이다.
> 우리는 이 'Trusted Context Poisoning'을 체계적으로 분석한 최초의 연구이다."

**Option B: "Agent Supply Chain Security" 관점**
> "소프트웨어 공급망 공격(SolarWinds, event-stream)의 AI 에이전트 버전.
> Git 저장소에 악성 instruction 파일을 배치하면, 
> 해당 저장소를 사용하는 모든 개발자의 AI 에이전트가 감염된다.
> 우리는 이 공격의 실현 가능성, 에이전트/모델별 취약성, 
> 기존 방어 메커니즘의 효과를 체계적으로 평가한다."

**Option C: 둘 다 합치기 (추천)**
> "SkillPoison: Trusted Context Poisoning as a Supply Chain Attack 
> on AI Coding Agents"

---

## 4. 기여(Contribution) 재정리

### 강한 기여 (자신 있게 주장 가능)

| # | 기여 | 근거 |
|---|------|------|
| C1 | **새로운 위협 모델 정의** — Trusted Context Poisoning | 기존 PI 연구와 구분되는 공격 벡터. 소스코드로 실증. |
| C2 | **에이전트 프레임워크 보안 비교** — 6종 소스코드 분석 | 모델이 아닌 프레임워크의 보안 아키텍처를 처음으로 체계적 비교 |
| C3 | **교차 에이전트 오염 발견 및 실증** | OpenCode의 11개 경로 자동 로드 — 완전히 새로운 공격 벡터 |
| C4 | **Skill 보안 스캐너 평가** | OpenClaw scanner의 우회 가능성 실증 — 방어 도구의 한계 |
| C5 | **실증 데이터** — 모델×에이전트×패턴별 ASR | 향후 연구/방어 설계를 위한 벤치마크 데이터 |

### 보조 기여 (추가 가치)

| # | 기여 |
|---|------|
| C6 | 악성 Skill Taxonomy (L1~L5 + A1~A3) |
| C7 | 12종 악성 Skill 데이터셋 (재현 가능) |
| C8 | 방어 가이드라인 (에이전트 개발자용) |

---

## 5. 결론: 차별점은 있는가?

**있다.** 하지만 "더 많은 모델을 테스트했다"나 "실제 에이전트를 사용했다" 같은 **양적 차이**가 아니라, 
**공격 벡터 자체가 다르다**는 **질적 차이**가 핵심이다:

```
기존 연구:  외부 데이터 → [비신뢰 컨텍스트] → 모델
SkillPoison: 프로젝트 파일 → [신뢰된 컨텍스트] → 모델
                ↑                    ↑
           Supply Chain          Instruction Hierarchy 우회
           (persistent,          (시스템 프롬프트 레벨)
            scalable)
```

**핵심 메시지:** "당신이 git clone한 프로젝트에 AGENTS.md가 있다면, 
당신의 AI 코딩 에이전트는 이미 공격자의 지시를 따르고 있을 수 있다."
