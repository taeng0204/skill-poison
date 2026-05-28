# OpenClaw & NanoClaw 소스코드 분석 보고서

> 분석 일자: 2026-03-31
> OpenClaw: https://github.com/openclaw/openclaw (⭐341k, TypeScript)
> NanoClaw: https://github.com/qwibitai/nanoclaw (TypeScript, 경량 대안)

---

## 1. OpenClaw — "Your own personal AI assistant"

### 1.1 프로젝트 개요
- **성격:** 코딩 에이전트가 아닌 **개인 AI 비서** (WhatsApp, Telegram, Discord 등 25+ 채널 지원)
- **규모:** 50만+ LOC, 70+ 의존성, 23k+ 커밋
- **핵심 차별점:** 멀티채널 + 플러그인/스킬 생태계 + 메모리 시스템
- **SkillPoison 관점:** 코딩 에이전트와 성격은 다르지만, **Skill/Plugin 시스템이 있어 악성 Skill 주입 연구에 매우 적합**

### 1.2 ✅ 보안 강점: Skill Scanner (유일한 에이전트!)

**소스:** `src/security/skill-scanner.ts`

OpenClaw은 분석한 에이전트 중 **유일하게** Skill 설치 시 보안 스캔을 수행:

```typescript
// LINE_RULES — 라인 단위 패턴 매칭
const LINE_RULES: LineRule[] = [
  {
    ruleId: "dangerous-exec",
    severity: "critical",
    message: "Shell command execution detected (child_process)",
    pattern: /\b(exec|execSync|spawn|spawnSync|execFile|execFileSync)\s*\(/,
    requiresContext: /child_process/,
  },
  {
    ruleId: "dynamic-code-execution",
    severity: "critical",
    message: "Dynamic code execution detected",
    pattern: /\beval\s*\(|new\s+Function\s*\(/,
  },
  // 크립토마이닝 탐지
  { pattern: /stratum\+tcp|stratum\+ssl|coinhive|cryptonight|xmrig/i },
  // WebSocket 비표준 포트 탐지
  { pattern: /new\s+WebSocket\s*\(\s*["']wss?:\/\/[^"']*:(\d+)/ },
];

// SOURCE_RULES — 소스 전체 패턴 매칭 (컨텍스트 기반)
const SOURCE_RULES: SourceRule[] = [
  // 파일 읽기 + HTTP 전송 = 데이터 유출 탐지
  { pattern: /readFileSync|readFile/, requiresContext: /\bfetch\b|\bpost\b|http\.request/i },
  // 헥스 인코딩 난독화 탐지
  { pattern: /(\\x[0-9a-fA-F]{2}){6,}/ },
  // Base64 대량 인코딩 탐지
  { pattern: /(?:atob|Buffer\.from)\s*\(\s*["'][A-Za-z0-9+/=]{200,}["']/ },
  // 환경변수 접근 + 외부 전송 = 정보 유출 탐지
  { pattern: /process\.env/, requiresContext: /\bfetch\b|\bpost\b|http\.request/i },
];
```

**스캔 결과에 따른 조치:**
- `critical` 발견 시 → **설치 차단** (`security_scan_blocked`)
- `warn` → 경고 표시
- `info` → 정보 표시

### 1.3 🟡 보안 스캔의 한계 (SkillPoison 공격 가능 지점)

| 한계 | 우회 방법 | SkillPoison 활용 |
|------|----------|-----------------|
| **JavaScript/TypeScript만 스캔** | Markdown Skill (지시 기반)은 스캔 대상 아님 | L4(사회공학) 패턴에 효과적 |
| **정적 패턴 매칭** | 다단계 인코딩, 문자열 조합으로 우회 | L5(은밀조작) 패턴 테스트 |
| **컨텍스트 기반 룰 제한적** | `process.env`만 감시 → `os.environ` (Python) 미탐지 | 언어 간 우회 |
| **Skill 내 마크다운 지시 미스캔** | "이 코드를 실행하라" 형태의 자연어 지시 | 가장 큰 공격 표면 |
| **설치 시에만 스캔** | 설치 후 동적 업데이트/변조 미감시 | Rug pull 공격 |

### 1.4 Skill 구조

**소스:** `src/agents/skills/`

```
skills/
├── config.ts          — Skill 설정 해석
├── env-overrides.ts   — 환경변수 오버라이드
├── filter.ts          — Skill 필터링
├── frontmatter.ts     — YAML 프론트매터 파싱
├── types.ts           — 타입 정의
└── workspace.ts       — 워크스페이스 Skill 로딩
```

- Skill은 `SkillEntry` 타입으로 관리
- `buildWorkspaceSkillsPrompt()` → Skill 내용을 에이전트 프롬프트에 주입
- `filterWorkspaceSkillEntries()` → 허용 목록 기반 필터링
- `syncSkillsToWorkspace()` → 원격 Skill 동기화

### 1.5 Plugin 시스템

**소스:** `src/plugins/`

- 1,700+ 줄의 복잡한 Plugin 로더
- npm 패키지, 로컬 파일, 아카이브 등 다양한 설치 경로
- Plugin은 `jiti`로 동적 로딩 (JIT TypeScript import)
- **`install-security-scan.runtime.ts`**: 설치 전 보안 스캔 (위 참조)
- **MCP 서버 지원**: Plugin이 MCP 도구를 노출 가능

---

## 2. NanoClaw — "Small enough to understand"

### 2.1 프로젝트 개요
- **성격:** OpenClaw의 경량 대안, **컨테이너 격리에 중점**
- **규모:** 의도적으로 작은 코드베이스 (< 35k 토큰)
- **핵심 철학:** "OpenClaw has nearly half a million lines of code... NanoClaw provides that same core functionality, but in a codebase small enough to understand"

### 2.2 ✅ 보안 강점: 컨테이너 격리

**소스:** `setup/container.ts`, `container/agent-runner/`

```
NanoClaw 보안 모델:
┌─────────────────────────┐
│ Host (NanoClaw gateway)  │
│  ┌───────────────────┐  │
│  │ Container         │  │ ← Apple Container / Docker
│  │  ┌─────────────┐  │  │
│  │  │ Claude Agent │  │  │ ← 파일시스템 격리
│  │  │ (agent-runner)│ │  │ ← 마운트된 것만 접근 가능
│  │  └─────────────┘  │  │
│  └───────────────────┘  │
└─────────────────────────┘
```

- **Apple Container** (macOS) 또는 **Docker** 기반 OS 수준 격리
- 에이전트는 컨테이너 내에서만 실행
- 명시적으로 마운트된 디렉토리만 접근 가능
- "Bash access is safe because commands run inside the container, not on your host"

### 2.3 🟡 보안 한계

| 항목 | 상태 |
|------|------|
| Skill 내용 검증 | ❌ 없음 (OpenClaw의 skill-scanner 미포함) |
| Skill 파일 무결성 | ❌ 없음 |
| 네트워크 격리 | ⚠️ 컨테이너 수준 (설정에 따라 다름) |
| Supply chain 보호 | ❌ 없음 (fork 기반이라 사용자 책임) |

### 2.4 SkillPoison 관점에서의 가치

NanoClaw는 **"컨테이너 격리가 악성 Skill을 얼마나 효과적으로 차단하는가"**를 테스트하기에 이상적:
- 컨테이너 안에서도 데이터 유출이 가능한가? (마운트된 디렉토리 경유)
- 사회공학적 공격은 컨테이너 격리를 우회할 수 있는가?
- 컨테이너 탈출 시도는 탐지되는가?

---

## 3. 전체 에이전트 비교 (6종 최종)

| 보안 항목 | Codex CLI | Aider | OpenCode | OpenClaw | NanoClaw | Claude Code |
|-----------|-----------|-------|----------|----------|----------|-------------|
| **Skill 내용 스캔** | ❌ | ❌ | ❌ | ✅ (유일!) | ❌ | ❌ |
| **자동 로드 파일** | 2 | 0 | **11** | Skill 시스템 | Skill 시스템 | 2 |
| **교차 에이전트 로드** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **명령 실행 샌드박싱** | ✅✅ | ❌ | ❌ | ⚠️ 앱레벨 | ✅✅ 컨테이너 | ⚠️ |
| **네트워크 격리** | ✅ | ❌ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| **무결성 검증** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Supply chain 보호** | ❌ | ❌ | ❌ | ⚠️ 스캔 | ❌ | ❌ |

### 보안 수준 종합 랭킹

```
1. Codex CLI    — seatbelt/landlock + iptables + 위험명령 탐지
2. NanoClaw     — OS 수준 컨테이너 격리 (but Skill 스캔 없음)
3. OpenClaw     — Skill 보안 스캔 (but 앱 레벨 격리)
4. Claude Code  — 사용자 확인 기반 (allowlist)
5. OpenCode     — 블랙리스트 (쉽게 우회) + 11개 자동 로드
6. Aider        — shell=True + 보안 메커니즘 전무
```

## 4. SkillPoison 실험 업데이트 제안

### 에이전트 분류 체계

| 카테고리 | 에이전트 | 특징 |
|----------|---------|------|
| **코딩 에이전트** | Codex, Aider, OpenCode, Claude Code | 코드 생성/편집 특화 |
| **범용 AI 비서** | OpenClaw, NanoClaw | 멀티채널/멀티태스크 |

### 실험 설계 시사점

1. **OpenClaw의 skill-scanner를 우회하는 악성 패턴 테스트** → 스캐너의 탐지율/우회율 측정
2. **NanoClaw의 컨테이너 격리 효과 측정** → 컨테이너 안에서도 유효한 공격 패턴 식별
3. **교차 에이전트 오염 (OpenCode)** → 하나의 악성 파일로 여러 에이전트 동시 공격
4. **보안 수준별 ASR 비교** → Codex(높음) vs Aider(없음) 간 ASR 차이
