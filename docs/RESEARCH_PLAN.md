# SkillPoison 연구 계획서 (최종)

## 1. 연구 배경 및 동기

### 1.1 문제 정의

AI 코딩 에이전트(Codex CLI, Claude Code, OpenCode, Aider 등)는 **Skill/Instruction 파일**을 시스템 프롬프트에 자동 주입하여 에이전트 행동을 커스터마이즈한다. 이 파일들은 에이전트가 "개발자의 신뢰된 지시"로 취급한다.

**위협:** 공격자가 Git 저장소, 템플릿, 패키지 등을 통해 이 파일에 악성 지시를 삽입하면:
- 에이전트가 이를 시스템 레벨 지시로 인식 → **Instruction Hierarchy 방어 무력화**
- Git 저장소에 잔존 → **Persistent 공격**
- 다수 개발자가 clone → **Scalable 공격**
- 하나의 파일이 여러 에이전트에 적용 → **Cross-agent 오염**

### 1.2 기존 연구와의 차이

| | 기존 Prompt Injection 연구 | **SkillPoison (본 연구)** |
|---|---|---|
| 공격 소스 | 비신뢰 외부 데이터 | **신뢰된 프로젝트 파일** |
| 신뢰 수준 | User/Third-party level | **System level** |
| Instruction Hierarchy | 방어 가능 | **구조적 우회** |
| 지속성 | 일회성 (런타임) | **Persistent (Git에 잔존)** |
| 확장성 | 개별 타겟 | **다수 개발자 동시 감염** |

### 1.3 위협 모델 (Threat Model)

**공격자:** 오픈소스 기여자, 패키지 배포자, 또는 저장소 접근 권한을 가진 내부자.
**공격 경로:** Git 저장소에 악성 instruction 파일(AGENTS.md, CLAUDE.md, .cursorrules 등) 배치.
**피해자:** 해당 저장소에서 AI 코딩 에이전트를 사용하는 개발자.
**가정:**
- 피해자는 git clone 후 에이전트를 실행 (일반적 개발 워크플로우)
- 에이전트는 instruction 파일을 자동으로 로드 (6종 에이전트 모두 확인됨)
- 피해자는 instruction 파일 내용을 세밀하게 검토하지 않음 (현실적)

---

## 2. 연구 질문

| RQ | 질문 | 관련 기여 |
|----|------|----------|
| **RQ1** | Trusted Context Poisoning은 Instruction Hierarchy 방어를 실제로 우회하는가? | C1 |
| **RQ2** | 에이전트 프레임워크의 보안 아키텍처(샌드박싱, 스캐닝)가 이 공격을 완화하는가? | C2, C3, C5 |
| **RQ3** | 오픈소스 vs 상용 모델 간 악성 Skill 취약성 차이는? | C3 |
| **RQ4** | 악성 Skill의 severity/stealth에 따른 공격 성공률 변화는? | C3 |
| **RQ5** | 교차 에이전트 오염은 실질적 위협인가? | C4 |

---

## 3. 연구 방법론

### Phase 1: 에이전트 정찰 ✅ 완료

6종 에이전트의 소스코드를 직접 분석하여 Skill 로딩 메커니즘, 샌드박싱, 보안 검증 수준 비교.

**핵심 발견:**
- 전 에이전트 Skill 내용 무검증 주입
- OpenCode: 11개 경로 자동 로드 + 교차 에이전트 파일 로드
- OpenClaw: 유일한 Skill Scanner (JS/TS만, Markdown 미스캔)
- Codex: 최고 수준 샌드박스 (seatbelt/landlock + iptables)
- Aider: 보안 메커니즘 전무 (shell=True)

### Phase 2: 악성 Skill Taxonomy ✅ 완료

12개 실제 공격 패턴 수집 → L1~L5 + A1~A3 분류 → 12종 악성 Skill 생성.

**Taxonomy:**
```
L1: 정보 유출       A1: Supply Chain 공격
L2: 코드 조작       A2: Scanner 우회
L3: 시스템 침투     A3: Sandbox 우회
L4: 사회 공학
L5: 은밀한 조작
```

### Phase 3: 실험 ⬜ 예정

**Pilot:** 3모델 × 7스킬 × 3에이전트 × 3반복 = 189 세션
**Full:** 8모델 × 12스킬 × 3에이전트 × 3반복 = 864 세션

**측정:** ASR, DRR, Task Completion Rate, Execution Completeness, Stealth Maintenance

### Phase 4: 분석 ⬜ 예정

정량 분석 (히트맵, 회귀분석, Kruskal-Wallis) + 정성 분석 (거부 패턴, 부분 실행 사례)

### Phase 5: 모델링 ⬜ 예정

수집 데이터 기반 악성 Skill 탐지 모델 개발 + 벤치마크 구성

---

## 4. 예상 기여

| # | 기여 | 유형 | 근거 |
|---|------|------|------|
| C1 | **Trusted Context Poisoning 위협 모델** | Conceptual | Instruction Hierarchy 우회 메커니즘 정의. 기존 PI와 질적 차이 논증 |
| C2 | **AI Agent Supply Chain Attack 실증** | Empirical | Git 저장소 → instruction 파일 → 에이전트 감염 경로의 실현 가능성 입증 |
| C3 | **6종 에이전트 보안 비교** | Empirical | Codex~Aider 보안 스펙트럼에서 모델×에이전트별 ASR 데이터 |
| C4 | **교차 에이전트 오염 발견** | Empirical | OpenCode의 11개 경로 자동 로드 → 다중 에이전트 동시 감염 |
| C5 | **Skill Scanner 한계 실증** | Empirical | OpenClaw scanner의 Markdown/비JS 우회 가능성 |
| C6 | **방어 가이드라인** | Defensive | Skill 서명, 내용 검증, 교차 에이전트 격리 등 설계 원칙 |

---

## 5. 타임라인

```
Phase 1-2 (완료):  연구 기반 구축
Week 6~:          Phase 3 실험 데이터 수집 시작
Week 6-9:         실험 실행 (Pilot → Full)
Week 10-11:       Phase 4 분석
Week 12-14:       Phase 5 모델링 + 논문 작성
```

---

## 6. 대상 학회

| 학회 | 마감 | 적합성 |
|------|------|--------|
| USENIX Security 2027 | ~2026 가을 | ✅ 시스템 보안 + 실증 |
| IEEE S&P 2027 | ~2026 가을 | ✅ 보안 최상위 |
| ACM CCS 2026 | ~2026 봄 | ✅ 컴퓨터 보안 |
| NDSS 2027 | ~2026 여름 | ✅ 네트워크/시스템 보안 |
| NeurIPS SaTML 2026 | ~2026 가을 | ✅ AI 안전/보안 워크숍 |
