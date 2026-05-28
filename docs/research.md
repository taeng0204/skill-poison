## ProtectSkills/MaliciousAgentSkillsBench

### **malicious_skills.csv**

**패턴 빈도**

| **패턴** | **개수** | **비율** | **의미** |
| --- | --- | --- | --- |
| Remote Code Execution | 118 | 75.2% | 외부/로컬 코드를 실행해 payload를 작동 |
| Network sniffing / Credential theft | 101 | 64.3% | credential, token, secret, 네트워크/환경 정보 탈취 |
| Behavior Manipulation | 100 | 63.7% | agent가 묻지 않고 실행하거나 특정 판단을 하도록 유도 |
| External Transmission | 79 | 50.3% | 외부 endpoint로 데이터 전송 |
| Context Leakage | 29 | 18.5% | agent context, 대화/작업 맥락 노출 |
| Instruction Override | 24 | 15.3% | 기존 instruction/safety rule 무시 지시 |
| Hidden Instructions | 15 | 9.6% | 주석/숨김 영역에 지시문 은닉 |
| Code Obfuscation | 15 | 9.6% | Base64, eval 등으로 로직 은닉 |
| File System Scan | 12 | 7.6% | 민감 파일/디렉터리 탐색 |
| Hardcoded Tokens | 10 | 6.4% | 토큰/비밀값 하드코딩 |
| Privilege Escalation | 6 | 3.8% | 권한 상승 시도 |
| Data Exfiltration | 5 | 3.2% | 데이터 유출 행위 명시 |
| Unpinned Dependencies | 5 | 3.2% | 고정되지 않은 의존성으로 supply-chain 위험 유발 |
| Excessive Permissions | 4 | 2.5% | 기능 대비 과도한 권한 요구 |

Network sniffing / Credential theft, External Transmission, Context Leakage, Data Exfiltration, Hardcoded Tokens가 묶입니다. 특히 credential theft와 외부 전송의 조합이 강합니다. “민감정보 수집 → 외부 전송” 흐름이 데이터셋의 대표적인 악성 chain

<aside>
💡

**악성 행위 패턴을 가지고 있는 Skills 기반으로 실험**

- `상위 4개 항목의 Skills 기준으로 조금더 세분화 해보기`
    - 중복 태크 현황 파악 ← 아래랑 비슷하게
- `상위 4개 항목이 들어간 Skills 따로 뽑기`
    - 이렇게 했을때 공식 제공 패턴 몇개까지 생존하는지
</aside>

## RCE-118개 분석

| **주된 RCE 유형(Codex)** | **개수** | **의미** |
| --- | --- | --- |
| Credential theft and exfiltration RCE | 48 | RCE로 credential/token을 수집하고 외부로 전송하는 유형 |
| Credential theft RCE | 33 | RCE가 credential/network 정보 탈취와 결합된 유형 |
| External transmission RCE | 9 | RCE가 외부 서버 전송과 결합된 유형 |
| Obfuscated exfiltration RCE | 9 | 난독화된 payload가 탈취/전송과 결합된 유형 |
| Agent manipulation-only RCE | 7 | agent 행동 조작과 RCE가 결합됐지만 탈취/전송 라벨은 없는 유형 |
| Agent-context leakage RCE | 6 | agent context/작업 맥락 누출과 결합된 유형 |
| Standalone RCE | 4 | 동반 패턴 없이 RCE만 표시된 유형 |
| Filesystem reconnaissance RCE | 2 | 파일 시스템 탐색과 RCE가 결합된 유형 |

**가장 흔한 유형**

이 데이터셋의 RCE는 단순히 “코드 실행 가능”이 아니라, 대부분 **credential 탈취 또는 외부 전송을 위한 실행 수단**으로 쓰입니다. 특히 Network sniffing / Credential theft + External Transmission + Remote Code Execution 조합이 핵심입니다.

**동반 패턴 기준 다중 분류**

한 skill은 여러 유형에 동시에 속할 수 있습니다.

| **다중 라벨 - Codex 분류** | **개수** |
| --- | --- |
| Behavior Manipulation, Instruction Override, Hidden Instructions | 86 |
| Network sniffing / Credential theft, External Transmission | 54 |
| Credential theft RCENetwork sniffing / Credential theft | 34 |
| Context Leakage | 24 |
| External Transmission | 15 |
| Code Obfuscation | 13 |
| File System Scan | 7 |
| Privilege Escalation, Excessive Permissions | 6 |
| Supply-chain dependency RCEUnpinned Dependencies | 5 |
| Remote Code Execution만 존재 | 4 |
| Hardcoded Tokens | 3 |

즉 118개 RCE 중 상당수는 “RCE + agent 조작 + credential 탈취” 형태입니다. 이건 사용자가 보기엔 정상 skill처럼 보여도, agent에게 실행을 유도하고 그 결과로 민감정보를 수집/전송하는 구조라고 보면 됩니다

- RCE는 대부분 단독 취약점이라기보다 **다른 악성 목적을 달성하기 위해 같이 쓰이는 취약점**

<aside>
💡

**무조건 공식 기준으로 다중 라벨 분류**

- 악성 스킬들의 주요 특징들을 나름대로 분류
- 기존의 taxonomy와 실제 실험간의 분류 간극(연구적인 분류, 효과적인 분류 차이)
- 우리가 정의한 실질적인 위험
</aside>

**해석**

| **유형** | **포함 패턴** | **행동** | **결과** |
| --- | --- | --- | --- |
| Credential theft and exfiltration RCE | Remote Code Execution, Network sniffing / Credential theft, External Transmission | 코드를 실행해 token, API key, secret 등을 수집하고 외부 endpoint로 전송 | 계정 탈취, API 악용, 내부 시스템 접근 |
| Credential theft RCE | Remote Code Execution, Network sniffing / Credential theft | 실행된 코드가 환경변수, 인증 파일, 네트워크 정보 등을 수집 | credential 노출. 외부 전송은 별도 라벨로 확인되지 않음 |
| External transmission RCE | Remote Code Execution, External Transmission | 실행된 코드가 외부 서버와 통신하거나 데이터를 보냄 | 파일/결과/메타데이터 유출 가능 |
| Obfuscated exfiltration RCE | Remote Code Execution, Code Obfuscation, 보통 External Transmission 또는 Credential theft 동반 | 숨겨진 payload를 런타임에 복호화해 실행하고, 민감정보 수집/전송 수행 | 탐지 회피, 리뷰 우회, 은밀한 유출 |
| Agent manipulation-only RCE | Remote Code Execution, Behavior Manipulation 또는 Instruction Override 또는 Hidden Instructions | agent에게 실행을 강제/유도하거나 안전 확인을 우회하도록 지시 | 사용자의 명시적 승인 없이 위험 명령 실행 가능 |
| Agent-context leakage RCE | Remote Code Execution, Context Leakage, 종종 Hidden Instructions/Behavior Manipulation 동반 | 실행 과정에서 대화 내용, 작업 맥락, 코드, 문서 등을 외부로 노출 | 프롬프트/업무 정보/소스코드 유출 |
| Standalone RCE | Remote Code Execution 단독 | 동반 라벨 없이 원격/임의 코드 실행만 표시 | payload 목적은 불명확하지만 실행 권한 자체가 고위험 |
| Filesystem reconnaissance RCE | Remote Code Execution, File System Scan | 실행된 코드가 .ssh, .aws, .env, 설정 파일 등을 탐색 | 후속 credential theft나 exfiltration 준비 |
| Privilege/permission abuse RCE | Remote Code Execution, Privilege Escalation 또는 Excessive Permissions | 실행 코드가 더 높은 권한을 얻거나 불필요하게 넓은 권한을 사용 | 시스템 장악 범위 확대 |
| Supply-chain dependency RCE | Remote Code Execution, Unpinned Dependencies | 고정되지 않은 의존성이나 외부 패키지 경로를 통해 실행 코드 유입 | dependency hijacking, 악성 업데이트 주입 |
| Hardcoded secret-enabled RCE | Remote Code Execution, Hardcoded Tokens | 하드코딩된 token/secret을 이용해 실행 또는 외부 서비스 접근 | 공격자 인프라 접근, 권한 오용, 추적 회피 가능 |

**가장 위험한 조합**

특히 아래 조합은 거의 완성형 공격 흐름입니다.

`Behavior Manipulation
+ Remote Code Execution
+ Network sniffing / Credential theft
+ External Transmission`

1. Behavior Manipulation: agent가 묻지 않고 실행하도록 유도
2. Remote Code Execution: payload 실행
3. Network sniffing / Credential theft: token/API key/secret 수집
4. External Transmission: 수집한 정보를 외부로 전송

결과적으로 “agent를 속여 실행시키고, credential을 훔쳐, 외부로 빼내는” 구조입니다

## 1. 조사 요약

| 항목 | 필요한 내용 |
| --- | --- |
| 선행연구 파악 | 최근 agent 보안 연구가 무엇을 다뤘는지 확인 |
| 연구 공백 도출 | 기존 연구가 아직 직접 보지 않은 부분 확인 |
| 평가 기준 설계 | agent의 판단을 allow / review / block 등으로 기록 |
| 결과 해석 | agent별로 어떤 기준에서 수용·차단 차이가 나는지 분석 |

## 2. 기존 연구와의 차이

| 구분 | 기존 연구가 주로 본 것 | 우리가 볼 것 |
| --- | --- | --- |
| Prompt injection benchmark | 외부 문서나 tool output이 agent를 속이는지 | 악성 skill 자체를 agent가 받아들이는지 |
| Tool-use defense | 실행 중 tool call을 막을 수 있는지 | skill 적용 전후 agent decision이 어떻게 달라지는지 |
| Guardrail / scanner | 특정 입력이나 artifact를 탐지할 수 있는지 | 실제 agent가 어떤 이유로 허용/차단하는지 |
| Sandbox / permission control | 실행 피해를 줄일 수 있는지 | agent가 위험을 사전에 인지하는지, 런타임에만 막히는지 |
| Supply-chain research | 악성 skill 생태계가 존재하는지 | 같은 악성 skill corpus에 대한 agent별 수용률/차단률 차이 |

**핵심 차별점**

기존 연구는 대체로 “공격이 성공하는가” 또는 “방어기술이 막는가”를 봄

## 3. 최근 관련 연구 요약

| 연구/자료 | 연도 | 핵심 내용 | 특징 | 바로가기 |
| --- | --- | --- | --- | --- |
| AgentDojo | 2024 | tool을 쓰는 LLM agent가 untrusted data의 prompt injection에 얼마나 취약한지 평가하는 benchmark. realistic task와 security test case를 제공 | agent 보안 평가 benchmark의 대표 사례. 다만 malicious skill 수용/차단 자체가 초점은 아님 | [arXiv](https://arxiv.org/abs/2406.13352), [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html), [OpenReview](https://openreview.net/forum?id=m1YYAQjO3w) |
| InjecAgent | 2024 | tool-integrated LLM agent에 대한 indirect prompt injection 공격을 평가 | agent가 외부 지시에 의해 tool을 오용할 수 있음을 보여줌. skill acceptance 평가는 별도 공백 | [arXiv](https://arxiv.org/abs/2403.02691), [HF Paper](https://huggingface.co/papers/2403.02691) |
| RTBAS | 2025 | information-flow control로 tool call이 integrity/confidentiality를 침해하는지 판단하고, 위험할 때만 사용자 확인 요구 | “무조건 모든 tool call 확인”이 아니라 위험 흐름만 확인하는 방향. 내 실험의 runtime control 해석에 도움 | [arXiv](https://arxiv.org/abs/2502.08966), [PDF](https://arxiv.org/pdf/2502.08966) |
| Prompt Flow Integrity | 2025 | LLM agent에서 privilege escalation을 막기 위해 untrusted data 식별, least privilege, unsafe data flow 검증을 제안 | 악성 skill이 권한을 넓히거나 tool 흐름을 오염시키는 경우와 연결 | [arXiv](https://arxiv.org/abs/2503.15547), [PDF](https://arxiv.org/pdf/2503.15547) |
| CaMeL | 2025 | trusted query에서 control/data flow를 분리하고 capability로 unauthorized data flow를 차단 | agent가 공격당할 수 있다는 전제에서 시스템 레벨 방어를 설계한 연구. 내 연구의 “사전 판단 vs 실행 통제” 구분에 도움 | [arXiv](https://arxiv.org/abs/2503.18813), [PDF](https://arxiv.org/pdf/2503.18813), [GitHub](https://github.com/google-research/camel-prompt-injection) |
| Progent | 2025 | LLM agent의 tool privilege를 fine-grained policy로 제한하는 프레임워크 | agent가 허용한 skill도 tool 권한 정책으로 제한될 수 있음을 보여줌 | [arXiv](https://arxiv.org/abs/2504.11703), [PDF](https://arxiv.org/pdf/2504.11703) |
| ACE | 2025 | LLM-integrated app system에서 악성 app이 planning, execution, privacy를 침해하는 문제를 다룸 | 악성 skill을 “third-party app/artifact”로 볼 때 참고 가능 | [arXiv](https://arxiv.org/abs/2504.20984), [PDF](https://arxiv.org/pdf/2504.20984), [DBLP](https://dblp.org/rec/journals/corr/abs-2504-20984) |
| ASIDE | 2025 | instruction과 data를 embedding 수준에서 분리해 prompt injection 취약성을 줄이려는 접근 | 자연어 지시와 데이터의 경계 문제가 agent 판단에 중요하다는 근거 | [arXiv](https://arxiv.org/abs/2503.10566), [PDF](https://arxiv.org/pdf/2503.10566), [Project](https://kortukov.github.io/publication/2025-03-05-aside) |
| Snyk ToxicSkills | 2026 | Agent Skills 생태계를 대규모 스캔해 악성 payload, credential theft, prompt injection, exposed secret 문제를 보고 | 악성 skill이 실제 생태계 수준의 supply-chain 문제가 되었음을 보여주는 가장 직접적인 자료 | [Report](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) |
| Snyk clawdhub campaign | 2026 | OpenClaw marketplace에서 악성 skill이 reverse shell, credential theft, data exfiltration을 수행한 캠페인 분석 | agent skill이 실제로 malware 유통 경로가 될 수 있음을 보여줌 | [Analysis](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/) |

## 4. 최근 연구 흐름

| 흐름 | 설명 | 대표 연구 |
| --- | --- | --- |
| Agent benchmark | agent가 tool을 쓸 때 prompt injection에 얼마나 취약한지 평가 | [AgentDojo](https://arxiv.org/abs/2406.13352), [InjecAgent](https://arxiv.org/abs/2403.02691) |
| Information-flow defense | 민감 데이터가 외부 sink로 흘러가는지 추적 | [RTBAS](https://arxiv.org/abs/2502.08966), [CaMeL](https://arxiv.org/abs/2503.18813) |
| Privilege / permission control | agent가 필요한 tool만 쓰도록 권한을 세분화 | [Progent](https://arxiv.org/abs/2504.11703), [Prompt Flow Integrity](https://arxiv.org/abs/2503.15547) |
| Instruction-data separation | instruction과 untrusted data를 분리해 prompt injection 완화 | [ASIDE](https://arxiv.org/abs/2503.10566), [Spotlighting](https://www.microsoft.com/en-us/research/publication/defending-against-indirect-prompt-injection-attacks-with-spotlighting/), [StruQ](https://arxiv.org/abs/2402.06363) |
| Skill supply-chain security | agent skill 자체가 악성 artifact가 될 수 있음을 분석 | [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/), [clawdhub campaign](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/) |

## 5. 남아 있는 연구 공백

| 연구 공백 | 왜 아직 부족한가 | 우리 연구에서 가능할 만한 것 |
| --- | --- | --- |
| Agent별 skill 수용/차단 비교 부족 | 기존 연구는 agent 공격 성공률이나 방어 프레임워크 중심 | 같은 악성 skill을 여러 agent에 적용해 수용률/차단률 비교 |
| 설치/적용 단계의 판단 연구 부족 | AgentDojo류 benchmark는 실행 중 prompt injection에 초점 | agent가 skill을 읽는 순간 어떤 위험 신호를 인지하는지 분석 |
| 설명과 실제 행동의 불일치 | agent가 “위험하다”고 말해도 실제로는 허용할 수 있음 | decision_reason과 actual_decision을 분리 기록 |
| 자연어 지시 + 코드 + 권한의 결합 평가 부족 | scanner는 코드, prompt guard는 텍스트에 치우치기 쉬움 | skill artifact 전체를 보고 agent가 어떻게 판단하는지 비교 |
| 조건부 허용 분석 부족 | 기존 연구는 공격 성공/실패 이분법이 많음 | block / review / allow_with_restrictions / allow로 세분화 |
| 런타임 통제와 사전 판단 구분 부족 | sandbox가 막은 것인지 agent가 판단한 것인지 섞일 수 있음 | accepted_by_agent와 blocked_by_runtime_control을 별도 기록 |

## 6. 가능한 질문

| RQ | 질문 | 측정값 |
| --- | --- | --- |
| RQ1 | 각 AI agent는 악성 skill을 얼마나 수용하거나 차단하는가? | agent별 block / review / restricted allow / allow 비율 |
| RQ2 | agent가 차단할 때 어떤 근거를 드는가? | decision_reason, matched_defense_signal |
| RQ3 | agent가 놓치는 위험 신호는 무엇인가? | missed_pattern, false allow 사례 |
| RQ4 | agent의 설명과 실제 행동은 일치하는가? | reason-action consistency |
| RQ5 | 동일 skill에 대해 agent별 판단 차이가 나타나는가? | agent 간 decision disagreement |
| RQ6 | 외부 scanner/guardrail을 붙이면 판단이 개선되는가? | baseline vs defended condition 차이 |
| RQ7 | 사전 차단과 런타임 차단 중 어디에서 주로 막히는가? | acceptance stage, execution stage, egress stage |

## 7. 결론

최근 연구들은 agent prompt injection, tool misuse, information-flow control, privilege control, skill supply-chain 위험을 빠르게 다루고 있음. 하지만 아직 **여러 AI agent가 같은 악성 skill을 보고 어떤 것은 받아들이고 어떤 것은 거르는지**를 체계적으로 비교한 연구는 부족함.

→기존 연구의 방어기술을 배경으로 삼되, 초점을 **agent별 malicious skill acceptance/rejection behavior**에 두기

## 참고자료

- [AgentDojo, NeurIPS 2024](https://arxiv.org/abs/2406.13352)
- [InjecAgent](https://arxiv.org/abs/2403.02691)
- [RTBAS](https://arxiv.org/abs/2502.08966)
- [Prompt Flow Integrity](https://arxiv.org/abs/2503.15547)
- [CaMeL: Defeating Prompt Injections by Design](https://arxiv.org/abs/2503.18813)
- [Progent](https://arxiv.org/abs/2504.11703)
- [ACE](https://arxiv.org/abs/2504.20984)
- [ASIDE](https://arxiv.org/abs/2503.10566)
- [Spotlighting](https://www.microsoft.com/en-us/research/publication/defending-against-indirect-prompt-injection-attacks-with-spotlighting/)
- [StruQ](https://arxiv.org/abs/2402.06363)
- [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)
- [Snyk clawdhub campaign](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/)
- [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/)
- [MCP Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
