# Phase 1 종합 보고서: Agent 환경 정찰 (Reconnaissance)

> 작성일: 2026-03-31
> 프로젝트: SkillPoison — Benchmarking Malicious Skill Vulnerability in Agentic LLM Environments

---

## 1. 개요

Phase 1에서는 6종의 에이전트 프레임워크 소스코드를 직접 분석하고, 관련 선행연구 6편을 서베이하여 다음 질문에 답했다:

> **"Agentic Tool(코딩 에이전트/AI 비서) 프레임워크 자체에 어떤 취약점 패턴이 존재하는가?"**

### 분석 대상

| # | 에이전트 | 유형 | GitHub ⭐ | 언어 | 소스 분석 |
|---|----------|------|-----------|------|-----------|
| 1 | Codex CLI | 코딩 에이전트 | 68k | Rust | ✅ 완료 |
| 2 | Aider | 코딩 에이전트 | 30k+ | Python | ✅ 완료 |
| 3 | OpenCode | 코딩 에이전트 | - | Go | ✅ 완료 |
| 4 | Claude Code | 코딩 에이전트 | - | (비공개) | ⚠️ 공개 문서 기반 |
| 5 | OpenClaw | AI 비서 | **341k** | TypeScript | ✅ 완료 |
| 6 | NanoClaw | AI 비서 | - | TypeScript | ✅ 완료 |

---

## 2. 핵심 발견 (Key Findings)

### Finding 1: 전 에이전트 Skill 내용 무검증 주입

**모든 에이전트**가 Skill/Instruction 파일 내용을 시스템 프롬프트에 **검증 없이** 주입한다.

| 에이전트 | 로딩 코드 | 검증 |
|----------|----------|------|
| Codex CLI | `fs::read_to_string()` → `ResponseItem` | ❌ |
| Aider | `io.read_text()` → 시스템 프롬프트 | ❌ |
| OpenCode | `os.ReadFile()` → `"Make sure to follow"` | ❌ |
| OpenClaw | `buildWorkspaceSkillsPrompt()` | ⚠️ JS/TS만 스캔 |
| NanoClaw | Skill 내용 → 에이전트 프롬프트 | ❌ |
| Claude Code | `CLAUDE.md` → 시스템 프롬프트 | ❌ |

**의미:** 악성 Skill이 주입되면, 모든 에이전트가 이를 신뢰된 지시로 처리한다.

### Finding 2: 보안 수준 스펙트럼이 극단적으로 넓음

```
보안 수준    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

Codex CLI   ████████████████████████████████░░░░░░░░  (80%) seatbelt + landlock + iptables
NanoClaw    ██████████████████████░░░░░░░░░░░░░░░░░░  (55%) 컨테이너 격리
OpenClaw    █████████████████░░░░░░░░░░░░░░░░░░░░░░░  (45%) Skill 스캐너
Claude Code ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (30%) 사용자 확인
OpenCode    ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (20%) 블랙리스트만
Aider       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (5%)  전무
```

**의미:** 실험에서 에이전트 간 ASR 차이가 유의미하게 나타날 가능성 높음.

### Finding 3: OpenCode의 교차 에이전트 오염

OpenCode만의 독특한 위험 — **11개 경로**의 instruction 파일을 자동 로드:

```
.github/copilot-instructions.md  ← GitHub Copilot용
.cursorrules                      ← Cursor용
.cursor/rules/                    ← Cursor용 (디렉토리 재귀)
CLAUDE.md, CLAUDE.local.md        ← Claude Code용
opencode.md, OpenCode.md, OPENCODE.md  ← OpenCode용
opencode.local.md, OpenCode.local.md, OPENCODE.local.md  ← OpenCode 로컬
```

**의미:** `.cursorrules` 하나로 **Cursor + OpenCode 동시 공격** 가능. "하나의 악성 파일, 다수의 에이전트" 시나리오.

### Finding 4: OpenClaw의 Skill Scanner — 유일한 방어이자 우회 대상

OpenClaw만 Skill 설치 시 보안 스캔 수행:

| 탐지 패턴 | 규칙 |
|-----------|------|
| Shell 실행 | `exec`, `spawn` + `child_process` 컨텍스트 |
| 동적 코드 실행 | `eval()`, `new Function()` |
| 크립토마이닝 | `stratum+tcp`, `coinhive`, `xmrig` |
| 데이터 유출 | `readFile` + `fetch`/`http.request` 동시 |
| 환경변수 탈취 | `process.env` + `fetch` 동시 |
| 난독화 | 긴 hex 시퀀스, 대량 Base64 |

**한계:**
- Markdown Skill (자연어 지시)은 스캔 대상 아님 → **L4(사회공학) 공격 미탐지**
- JavaScript/TypeScript만 스캔 → Python, Shell 스크립트 미탐지
- 정적 패턴 매칭 → 다단계 인코딩/문자열 조합으로 우회 가능
- 설치 시에만 스캔 → 설치 후 동적 변경 미감시

### Finding 5: 샌드박싱과 정보 유출의 간극

Codex CLI의 seatbelt/landlock 샌드박스조차 **정보 유출을 완전히 차단하지 못함**:

```
공격 경로: 악성 Skill → 모델이 파일 읽기 → 읽은 내용을 모델 응답에 포함
                                                    ↑
                                          샌드박스가 차단하지 않는 영역
```

- 파일 읽기 자체는 허용 (프로젝트 디렉토리 내)
- 모델이 읽은 내용을 "요약"이나 "분석"으로 위장하여 출력
- 사용자가 해당 출력을 외부에 공유하면 간접 유출

---

## 3. 에이전트별 세부 비교

### 3.1 Skill/Instruction 로딩

| 항목 | Codex | Aider | OpenCode | OpenClaw | NanoClaw | Claude Code |
|------|-------|-------|----------|----------|----------|-------------|
| Skill 파일명 | AGENTS.md | (수동) | 11종 | Skill 시스템 | Skill 시스템 | CLAUDE.md |
| 자동 로드 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 계층적 로드 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 교차 에이전트 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 내용 스캔 | ❌ | ❌ | ❌ | ✅ (JS/TS) | ❌ | ❌ |
| 무결성 검증 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 3.2 실행 환경 보안

| 항목 | Codex | Aider | OpenCode | OpenClaw | NanoClaw | Claude Code |
|------|-------|-------|----------|----------|----------|-------------|
| OS 샌드박스 | ✅ | ❌ | ❌ | ❌ | ✅ 컨테이너 | ❌ |
| 네트워크 격리 | ✅ iptables | ❌ | ⚠️ 블랙리스트 | ⚠️ | ⚠️ | ❌ |
| 위험 명령 탐지 | ✅ | ❌ | ⚠️ | ⚠️ | ❌ | ⚠️ |
| 자동 승인 위험 | ⚠️ | ⚠️ | ✅ env/printenv | ⚠️ | ❌ | ⚠️ |

### 3.3 Supply Chain 공격 노출

| 벡터 | Codex | Aider | OpenCode | OpenClaw | NanoClaw | Claude Code |
|------|-------|-------|----------|----------|----------|-------------|
| Git 저장소 오염 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 상위 디렉토리 상속 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 원격 Skill 설치 | ❌ | ❌ | ❌ | ✅ | ⚠️ | ❌ |
| 패키지 의존성 | ⚠️ | ❌ | ❌ | ✅ npm | ❌ | ❌ |

---

## 4. 선행연구 서베이 요약

| # | 논문 | 연도 | 핵심 | 우리 연구와의 Gap |
|---|------|------|------|-------------------|
| 1 | InjecAgent | 2024 | 간접 PI 벤치마크 (1054 케이스) | Skill 파일 자체의 악성 패턴 미다룸 |
| 2 | ToolSword | 2024 | 도구 사용 안전성 6가지 시나리오 | 도구 자체가 악성인 경우 미고려 |
| 3 | AgentDojo | 2024 | 동적 Agent 보안 프레임워크 | 코딩 에이전트/Skill 특화 부족 |
| 4 | MCP Invisible Threats | 2025 | MCP 스텔스 인젝션 | 오픈소스 모델 비교 부족 |
| 5 | Not What You've Signed Up For | 2023 | 실제 앱 간접 PI | Agent 환경 미다룸 |
| 6 | MCP RCE (Invariant Labs) | 2025 | MCP Tool Poisoning/Rug Pull | 정량적 벤치마크 없음 |

**⇒ 공통 Gap: "Skill 파일 자체에 내재된 악성 패턴"에 대한 체계적 연구 부재**

---

## 5. Phase 2를 위한 시사점

### 5.1 검증된 가설 (소스코드 분석으로 확인)

- **H1 ✅:** 모든 에이전트가 Skill 내용을 무검증으로 시스템 프롬프트에 주입
- **H3 ⚠️:** 샌드박스가 있어도 정보 유출은 차단 불가 (간접 경로)

### 5.2 Phase 3 실험으로 검증 필요한 가설

- **H2:** 오픈소스 모델이 상용 모델보다 악성 지시에 더 취약
- **H4:** 은밀한(stealth) 악성 Skill이 명시적 것보다 높은 ASR
- **H5:** 사회공학적 패턴이 기술적 패턴보다 효과적

### 5.3 Phase 2 악성 Skill Taxonomy에 반영할 새로운 패턴

소스코드 분석에서 발견된 **에이전트 특화 공격 벡터:**

| 패턴 | 대상 에이전트 | Taxonomy 분류 |
|------|-------------|---------------|
| AGENTS.md 계층적 오염 | Codex, Claude Code | L2 (Supply Chain) |
| .cursorrules 교차 오염 | OpenCode + Cursor | L2 (Supply Chain) |
| OpenClaw 스캐너 우회 (마크다운 지시) | OpenClaw | L5 (Stealth) |
| env/printenv 자동 승인 악용 | OpenCode | L1 (Data Exfil) |
| shell=True 직접 인젝션 | Aider | L3 (System Compromise) |
| 컨테이너 마운트 경유 유출 | NanoClaw | L1 (Data Exfil) |

---

## 6. 상세 분석 참조

- [Codex CLI + Aider 분석](agent-tools/ANALYSIS_REPORT.md)
- [OpenCode 분석](agent-tools/OPENCODE_ANALYSIS.md)
- [OpenClaw + NanoClaw 분석](agent-tools/OPENCLAW_NANOCLAW_ANALYSIS.md)
- [선행연구 서베이](literature/prior_work_survey.md)
- [에이전트 스캔 보고서 (JSON)](agent-tools/scan_report.json)
