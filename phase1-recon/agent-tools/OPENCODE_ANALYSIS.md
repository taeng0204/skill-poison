# OpenCode 소스코드 분석 보고서

> 분석 대상: https://github.com/opencode-ai/opencode
> 언어: Go
> 분석 일자: 2026-03-31

---

## 1. 🔴 Critical: 다중 Instruction 파일 자동 로드

**소스:** `internal/config/config.go:108-120`

```go
var defaultContextPaths = []string{
    ".github/copilot-instructions.md",
    ".cursorrules",
    ".cursor/rules/",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "opencode.md",
    "opencode.local.md",
    "OpenCode.md",
    "OpenCode.local.md",
    "OPENCODE.md",
    "OPENCODE.local.md",
}
```

**의미:** OpenCode는 **11개 경로**의 instruction 파일을 자동으로 탐색하고 로드한다.
특히 **다른 에이전트용 파일**(`CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`)까지 읽는다.

**🔴 공격 시나리오:**
- 공격자가 저장소에 `.cursorrules` (Cursor용)를 배치하면 OpenCode 사용자도 영향 받음
- 하나의 악성 instruction 파일로 **여러 에이전트 프레임워크를 동시에 타겟** 가능
- `CLAUDE.local.md` / `opencode.local.md`는 `.gitignore` 대상이라 로컬 공격에 활용 가능

## 2. 🔴 Critical: 내용 무검증 주입

**소스:** `internal/llm/prompt/prompt.go:131-137`

```go
func processFile(filePath string) string {
    content, err := os.ReadFile(filePath)
    if err != nil {
        return ""
    }
    return "# From:" + filePath + "\n" + string(content)
}
```

**의미:** 파일 내용을 `os.ReadFile()`로 읽어서 **그대로 시스템 프롬프트에 주입**.
- 악성 패턴 스캔: ❌ 없음
- 내용 새니타이징: ❌ 없음
- 크기 제한: ❌ 없음
- 사용자 확인: ❌ 없음

## 3. 🔴 Critical: 시스템 프롬프트에 "반드시 따르라" 지시

**소스:** `internal/llm/prompt/prompt.go:35`

```go
return fmt.Sprintf(
    "%s\n\n# Project-Specific Context\n Make sure to follow the instructions in the context below\n%s",
    basePrompt, contextContent,
)
```

**의미:** 모델에게 instruction 파일 내용을 **반드시 따르라**고 명시적으로 지시.
악성 Skill이 주입되면 모델이 이를 따를 가능성이 극대화됨.

## 4. 🟡 부분적 방어: Banned Commands

**소스:** `internal/llm/tools/bash.go:41-55`

```go
var bannedCommands = []string{
    "alias", "curl", "curlie", "wget", "axel", "aria2c",
    "nc", "telnet", "lynx", "w3m", "links", "httpie", "xh",
    "http-prompt", "chrome", "firefox", "safari",
}
```

**의미:** 네트워크 관련 명령어(`curl`, `wget`, `nc` 등)를 차단하는 블랙리스트.

**🟡 한계:**
- `python3 -c "import urllib.request; ..."` → 차단 안 됨
- `bash -c 'echo ... | base64 -d | sh'` → 간접 실행 가능
- `pip install malicious-package` → 차단 안 됨
- 블랙리스트 기반이라 우회 경로 다수 존재

## 5. 🟡 Permission 시스템

**소스:** `internal/permission/permission.go`

- 도구 실행 전 사용자 승인 요청 가능
- `AutoApproveSession()` 호출 시 해당 세션의 모든 요청 자동 승인
- **🔴 문제:** `safeReadOnlyCommands`에 `env`, `printenv` 포함 → 환경변수 자동 승인으로 조회 가능

## 6. 🟠 디렉토리 Traversal 가능

**소스:** `internal/llm/prompt/prompt.go:75-96`

`.cursor/rules/` 경로의 경우 `filepath.WalkDir()`로 하위 전체를 재귀 탐색:
```go
if strings.HasSuffix(p, "/") {
    filepath.WalkDir(filepath.Join(workDir, p), func(path string, d os.DirEntry, err error) error {
        // 모든 하위 파일 로드
    })
}
```

**🟠 위험:** `.cursor/rules/` 디렉토리에 다수의 악성 파일 배치 가능. 심볼릭 링크를 통한 디렉토리 탈출 가능성도 존재.

---

## 7. 종합 비교 (OpenCode 추가)

| 보안 항목 | Codex CLI | Aider | OpenCode |
|-----------|-----------|-------|----------|
| 내용 검증 | ❌ | ❌ | ❌ |
| 자동 로드 경로 수 | 2 (AGENTS.md, override) | 0 (수동) | **11개** (가장 넓음) |
| 교차 에이전트 파일 로드 | ❌ | ❌ | **✅ (CLAUDE.md, .cursorrules 등)** |
| "반드시 따르라" 지시 | ❌ | ❌ | **✅** |
| 네트워크 명령 차단 | ✅ iptables | ❌ | ⚠️ 블랙리스트 (우회 가능) |
| 명령 실행 샌드박싱 | ✅ seatbelt/landlock | ❌ | ❌ |
| 사용자 승인 | ⚠️ 부분적 | ⚠️ 부분적 | ⚠️ 부분적 (auto-approve 가능) |

## 8. SkillPoison 실험 시사점

### OpenCode 특이 공격 벡터 (Unique Attack Surface)

1. **Cross-agent poisoning:** `.cursorrules` 하나로 Cursor + OpenCode 동시 공격 가능
2. **"Make sure to follow" amplification:** 시스템 프롬프트에서 instruction 준수를 강제하므로 ASR 상승 예상
3. **Banned command bypass:** `python3 -c` 또는 `pip install`로 네트워크 제한 우회
4. **env/printenv auto-approve:** 환경변수 탈취가 승인 없이 가능
5. **Directory traversal via rules/:** `.cursor/rules/` 재귀 탐색으로 대량 악성 instruction 주입
