# SkillPoison 연구 계획서

## 1. 연구 배경

LLM 기반 코딩 에이전트(Claude Code, Codex CLI, OpenCode, Aider 등)는 **Skill/Plugin** 시스템을 통해 기능을 확장한다. 이 Skill 파일들은 보통 마크다운 형식으로 에이전트의 시스템 프롬프트에 주입되며, 도구 호출 패턴, 작업 절차, 코드 템플릿 등을 정의한다.

**위험:** 악성 행위자가 Skill 파일에 은밀한 악성 지시를 삽입하면, 에이전트가 이를 신뢰된 지시로 간주하고 실행할 수 있다. 이는 기존 Prompt Injection과 달리:
- **지속적** (Skill은 세션 전체에 걸쳐 로드됨)
- **은밀함** (정상적인 기술 문서처럼 위장 가능)
- **광범위** (공유 Skill 저장소를 통해 다수 사용자에게 전파 가능)

## 2. 연구 질문

### RQ1: Agent Tool 자체의 취약점
- 오픈소스 코딩 에이전트(OpenCode, Aider, Continue 등)의 Skill/Plugin 로딩 메커니즘에 어떤 보안 취약점이 있는가?
- Skill 파일의 검증/샌드박싱은 어떻게 이루어지는가 (또는 이루어지지 않는가)?

### RQ2: 악성 Skill Taxonomy
- 악성 Skill의 공격 패턴을 어떻게 분류할 수 있는가?
- 각 패턴의 은밀성(stealth), 위험도(severity), 탐지 난이도(evasion)는?

### RQ3: 모델별 취약성 차이
- 오픈소스 모델(Llama, Qwen, DeepSeek 등) vs 상용 모델(GPT-4, Claude, Gemini)의 악성 Skill 탐지/거부 능력 차이?
- 모델 크기(7B vs 70B vs 405B)에 따른 취약성 차이?

### RQ4: 악성 Skill 레벨/유형별 양상
- 보안 레벨(Low/Medium/High/Critical)에 따라 에이전트 행동이 어떻게 달라지는가?
- 어떤 유형의 악성 패턴이 가장 높은 공격 성공률(ASR)을 보이는가?

## 3. 연구 방법론

### Phase 1: 정찰 (Reconnaissance) — 2주
**목표:** 실험 파이프라인 자체의 취약점 패턴 분석

1. **에이전트 도구 취약점 조사**
   - 대상: OpenCode, Aider, Continue, Claude Code, Codex CLI
   - 분석 항목:
     - Skill/Plugin 로딩 경로 및 파싱 로직
     - 입력 검증/새니타이징 메커니즘
     - 샌드박싱 수준 (파일시스템, 네트워크, 프로세스)
     - 권한 상승 가능 경로
   - 기존 CVE/취약점 보고서 수집

2. **모델 자체의 취약점 조사**
   - Prompt Injection 저항성 벤치마크 결과 수집
   - 모델별 안전 정렬(alignment) 수준 비교
   - Instruction hierarchy 구현 여부

### Phase 2: 악성 Skill Taxonomy 구축 — 3주
**목표:** 악성 Skill 패턴 수집, 분류, 생성

1. **수집 (Collection)**
   - GitHub 공개 Skill 저장소 크롤링
   - CTF/보안 연구 커뮤니티의 PoC 수집
   - 기존 Prompt Injection 데이터셋 활용 (InjecAgent, TensorTrust 등)
   - 실제 MCP 서버 악성 사례 수집

2. **분류 (Classification)**
   ```
   악성 Skill Taxonomy
   ├── L1: 정보 유출 (Data Exfiltration)
   │   ├── 환경 변수/API 키 탈취
   │   ├── 파일 내용 외부 전송
   │   └── 대화 내용 유출
   ├── L2: 코드 조작 (Code Manipulation)
   │   ├── 백도어 삽입
   │   ├── 의존성 변조 (supply chain)
   │   └── 테스트 우회
   ├── L3: 시스템 침투 (System Compromise)
   │   ├── 리버스 쉘
   │   ├── 권한 상승
   │   └── 지속성 확보 (persistence)
   ├── L4: 사회 공학 (Social Engineering)
   │   ├── 사용자 기만 (misleading output)
   │   ├── 신뢰 악용 (trust exploitation)
   │   └── 확인 우회 (confirmation bypass)
   └── L5: 은밀한 조작 (Stealth Operations)
       ├── 지연 실행 (time-delayed)
       ├── 조건부 트리거
       └── 난독화된 페이로드
   ```

3. **생성 (Generation)**
   - 수집된 패턴 기반 변형 생성
   - 위험도 레벨별 (Low → Critical) 악성 Skill 세트 생성
   - 은밀성 수준별 변형 (명시적 → 은밀 → 고도 은밀)

### Phase 3: 실험 설계 및 실행 — 4주
**목표:** 체계적 실험으로 데이터 수집

1. **실험 설계**
   ```
   독립 변수:
   ├── 모델 (5-8종: GPT-4, Claude, Gemini, Llama-70B, Qwen-72B, DeepSeek-V3, ...)
   ├── 에이전트 프레임워크 (3-4종: OpenCode, Aider, Claude Code, Codex)
   ├── 악성 Skill 유형 (5 카테고리 × 3 하위 유형 = 15종)
   └── 위험도 레벨 (4단계: Low, Medium, High, Critical)
   
   종속 변수:
   ├── 공격 성공률 (ASR: Attack Success Rate)
   ├── 탐지/거부율 (Detection/Refusal Rate)
   ├── 실행 전 경고 여부 (Warning Rate)
   ├── 실행 완전성 (Execution Completeness)
   └── 은밀성 유지 여부 (Stealth Maintenance)
   
   통제 변수:
   ├── 동일 태스크 프롬프트
   ├── 동일 실행 환경 (Docker 격리)
   └── 반복 횟수 (3회 이상)
   ```

2. **실험 환경**
   ```
   ┌─────────────────────────────────────────┐
   │           Experiment Runner              │
   │  ┌─────────────────────────────────────┐ │
   │  │        Docker Sandbox               │ │
   │  │  ┌──────────┐  ┌────────────────┐   │ │
   │  │  │  Agent   │  │ Malicious Skill│   │ │
   │  │  │(OpenCode)│──│  (injected)    │   │ │
   │  │  └────┬─────┘  └────────────────┘   │ │
   │  │       │                             │ │
   │  │  ┌────┴─────┐  ┌────────────────┐   │ │
   │  │  │  Task    │  │   Monitor      │   │ │
   │  │  │Workspace │  │ (file/net/proc)│   │ │
   │  │  └──────────┘  └────────────────┘   │ │
   │  └─────────────────────────────────────┘ │
   │                                          │
   │  ┌──────────────────┐                    │
   │  │  Metrics Proxy   │ ← API 호출 추적   │
   │  │  (LiteLLM)       │                    │
   │  └──────────────────┘                    │
   │                                          │
   │  ┌──────────────────┐                    │
   │  │  Result Logger   │ ← 행동 기록       │
   │  │  (file/net/proc) │                    │
   │  └──────────────────┘                    │
   └─────────────────────────────────────────┘
   ```

3. **측정 방법**
   - **파일시스템 모니터링:** inotifywait로 생성/수정/삭제 파일 추적
   - **네트워크 모니터링:** tcpdump/mitmproxy로 외부 통신 감시
   - **프로세스 모니터링:** audit 로그로 실행된 명령어 추적
   - **API 로그:** LiteLLM proxy로 모든 LLM API 호출 기록
   - **에이전트 출력:** 전체 대화/행동 로그 저장

### Phase 4: 분석 — 2주
**목표:** 데이터 분석 및 시각화

1. **정량 분석**
   - 모델별 ASR 비교 (히트맵)
   - 위험도 레벨별 ASR 추이
   - 패턴 유형별 ASR 분포
   - 모델 크기 vs ASR 상관관계
   - 에이전트 프레임워크별 방어력 비교

2. **정성 분석**
   - 에이전트의 거부/경고 메시지 패턴 분류
   - 부분 실행 사례 분석
   - 은밀한 공격의 탐지 실패 사례 심층 분석

### Phase 5: 모델링 — 3주 (재윤 담당)
**목표:** 악성 Skill 탐지 모델 개발

- 수집된 데이터 기반 탐지 모델 학습
- 벤치마크 구성 및 평가

## 4. 타임라인

```
Week 1-2:  Phase 1 — 정찰
           └ 에이전트 도구 분석, 모델 취약점 조사, 선행연구 정리

Week 3-5:  Phase 2 — Taxonomy
           └ 악성 Skill 수집, 분류 체계 구축, 변형 생성

Week 6-9:  Phase 3 — 실험
           └ 실험 환경 구축, 실험 실행, 데이터 수집

Week 10-11: Phase 4 — 분석
           └ 메트릭 산출, 시각화, 보고서 작성

Week 12-14: Phase 5 — 모델링
           └ 탐지 모델 개발, 평가, 논문 작성
```

## 5. 예상 기여 (Expected Contributions)

1. **악성 Skill Taxonomy:** Agent 환경 악성 Skill의 체계적 분류 체계 최초 제안
2. **SkillPoison Benchmark:** 모델별/패턴별 취약성 측정 벤치마크 데이터셋
3. **Cross-model 분석:** 오픈소스 vs 상용 모델의 악성 Skill 취약성 비교 결과
4. **방어 가이드라인:** 에이전트 프레임워크 개발자를 위한 보안 권고사항

## 6. 대상 학회/저널

- **Tier 1:** USENIX Security, IEEE S&P, ACM CCS, NDSS
- **ML/AI:** NeurIPS (SaTML workshop), ICLR, AAAI
- **보안 특화:** RAID, ACSAC, AsiaCCS
