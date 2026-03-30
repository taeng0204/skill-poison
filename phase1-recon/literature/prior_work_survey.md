# SkillPoison 선행연구 서베이

## 1. InjecAgent (Zhan et al., 2024)

- **논문:** InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents
- **arXiv:** 2403.02691
- **핵심:** 도구 통합 LLM Agent에 대한 간접 Prompt Injection(IPI) 벤치마크
- **내용:**
  - 1,054개 테스트케이스, 17개 유저 도구, 62개 공격자 도구
  - 공격 의도: 직접 피해 (Direct Harm) + 데이터 유출 (Data Exfiltration)
  - 30개 LLM Agent 평가
- **주요 결과:**
  - ReAct-prompted GPT-4: 24% ASR
  - Hacking prompt 강화 시 ASR 거의 2배 증가
  - 모든 모델이 어느 정도 취약
- **한계 (우리 gap):**
  - ❌ 정적 벤치마크 (시뮬레이션된 도구, 실제 실행 아님)
  - ❌ Skill/Plugin 파일 자체의 악성 패턴 미다룸
  - ❌ 코딩 에이전트 특화 시나리오 없음
  - ❌ 오픈소스 모델 비교 제한적

## 2. ToolSword (Ye et al., 2024)

- **논문:** ToolSword: Unveiling Safety Issues of Large Language Models in Tool Learning Across Three Stages
- **arXiv:** 2402.10753
- **핵심:** LLM의 도구 사용 과정 3단계(입력, 실행, 출력)에서의 안전성 평가
- **내용:**
  - 6가지 안전 시나리오 평가
  - 악성 쿼리, 잘못된 도구 선택, 위험한 파라미터 등
- **주요 결과:**
  - GPT-4 포함 모든 LLM이 도구 사용 시 안전 실패
  - 입력 단계 > 실행 단계 > 출력 단계 순으로 취약
- **한계 (우리 gap):**
  - ❌ 도구 자체가 악성인 시나리오는 미고려
  - ❌ 모델의 "판단력"에 초점 (도구 자체의 위험성 아님)
  - ❌ Skill 파일 형태의 공격 미포함

## 3. AgentDojo (Debenedetti et al., 2024)

- **논문:** AgentDojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents
- **arXiv:** 2406.13352
- **핵심:** Agent 보안 평가를 위한 동적 프레임워크
- **내용:**
  - 97개 task, 629개 보안 테스트케이스
  - Prompt Injection 공격과 유틸리티를 동시 평가
  - 공격/방어 양쪽 확장 가능한 프레임워크
- **주요 결과:**
  - 최선의 방어도 공격 완전 차단 못함
  - 방어 적용 시 유틸리티 저하 발생 (trade-off)
- **한계 (우리 gap):**
  - ❌ 코딩 에이전트 특화 시나리오 부족
  - ❌ 악성 Skill/Plugin 패턴 분류 체계 없음
  - ❌ 오픈소스 모델 비교 부족

## 4. Invisible Threats from MCP (Shen et al., 2025)

- **논문:** Invisible Threats from Model Context Protocol: Generating Stealthy Injection Payload via Tree-based Adaptive Search
- **arXiv:** 2603.24203
- **핵심:** MCP 환경에서 스텔스 인젝션 페이로드 생성
- **내용:**
  - Tree-based Adaptive Search 알고리즘
  - MCP 도구 설명에 은닉된 악성 지시 삽입
  - 기존 방어(perplexity filter 등) 우회
- **주요 결과:**
  - 기존 방어를 우회하는 스텔스 공격 가능
  - 자동화된 공격 페이로드 생성 가능
- **한계 (우리 gap):**
  - ❌ MCP 특화 (일반 Skill 시스템 미포함)
  - ❌ 모델별 취약성 비교 부족
  - ❌ 공격 패턴 분류 체계 없음

## 5. Not What You've Signed Up For (Greshake et al., 2023)

- **논문:** Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection
- **arXiv:** 2302.12173
- **핵심:** 실제 LLM 통합 앱에 대한 간접 Prompt Injection 공격
- **내용:**
  - 이메일, 웹페이지 등 외부 콘텐츠를 통한 공격
  - 데이터 유출, 사회 공학, 스팸 등 다양한 공격 시나리오
- **주요 결과:**
  - 실제 앱(Bing Chat, ChatGPT Plugin)에서 공격 성공 입증
  - 간접 PI가 현실적 위협임을 최초로 체계적 증명
- **한계 (우리 gap):**
  - ❌ Agent/코딩 에이전트 환경 미다룸
  - ❌ Skill 시스템 특화 연구 아님
  - ❌ 모델 간 비교 없음

## 6. Compromising RCE in MCP Tools (invariantlabs, 2025)

- **출처:** Invariant Labs Blog / PoC
- **핵심:** MCP 도구를 통한 RCE(Remote Code Execution) 달성
- **내용:**
  - Tool Poisoning: 도구 설명에 악성 지시 삽입
  - Rug Pulls: 승인 후 도구 동작 변경
  - Cross-tool contamination
- **주요 결과:**
  - MCP 서버를 통해 실제 RCE 가능
  - 기존 보안 메커니즘 우회 가능
- **한계 (우리 gap):**
  - ❌ 특정 공격 벡터에 집중 (체계적 분류 없음)
  - ❌ 모델 간 비교 없음
  - ❌ 정량적 벤치마크 없음

---

## 연구 공백 요약 (Research Gap)

| 차원 | 기존 연구 현황 | SkillPoison이 채울 공백 |
|------|--------------|----------------------|
| **공격 벡터** | 간접 PI, 도구 설명 조작 | **Skill 파일 내 악성 패턴** |
| **실험 환경** | 시뮬레이션/API 호출 | **실제 Agent 프레임워크 동적 실험** |
| **모델 범위** | GPT-4 등 상용 위주 | **오픈소스 모델 포함 체계적 비교** |
| **분류 체계** | 공격 유형 산발적 | **악성 Skill Taxonomy (L1-L5)** |
| **세분화** | 성공/실패 이분법 | **위험도 레벨 × 은밀성 × 유형별 다차원 분석** |
| **에이전트 다양성** | 특정 도구 대상 | **다중 코딩 에이전트 프레임워크 비교** |

## 추가 조사 필요 논문

- [ ] TensorTrust (2024): 공격/방어 게임 기반 PI 벤치마크
- [ ] BIPIA (2024): 간접 PI 분석 벤치마크
- [ ] R-Judge (2024): Agent 안전성 판단 벤치마크
- [ ] ToolEmu (2024): Agent 도구 사용 시뮬레이터
- [ ] AgentHarm (2024): Agent 위험 행동 벤치마크
