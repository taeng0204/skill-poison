# Phase 1: 에이전트 프레임워크 소스코드 분석 보고서

> 분석 일자: 2026-03-31
> 분석 대상: Codex CLI (openai/codex), Aider (Aider-AI/aider)
> 목적: Skill/Instruction 로딩 메커니즘의 보안 취약점 패턴 식별

---

## 1. Codex CLI (OpenAI)

### 1.1 Skill 로딩 메커니즘

**소스 위치:** `codex-rs/core-skills/src/loader.rs`, `injection.rs`, `render.rs`

**핵심 발견:**
- Skill 파일(`SKILL.md`)은 YAML 프론트매터 + 마크다운 본문으로 구성
- `loader.rs`: 프론트매터에서 `name`, `description`, `metadata` 파싱 (Serde Deserialize)
- `injection.rs`: **파일 내용을 그대로 `fs::read_to_string()`으로 읽어 `ResponseItem`에 주입**
  ```rust
  // injection.rs:41-54 — 핵심 취약 코드
  match fs::read_to_string(&skill.path_to_skills_md).await {
      Ok(contents) => {
          result.items.push(ResponseItem::from(SkillInstructions {
              name: skill.name.clone(),
              path: skill.path_to_skills_md.to_string_lossy().into_owned(),
              contents,  // ← 내용 검증 없이 그대로 주입
          }));
      }
  }
  ```
- `render.rs`: Skill 목록을 시스템 프롬프트의 `## Skills` 섹션으로 렌더링
- **검증 없음:** Skill 내용에 대한 악성 패턴 검사, 새니타이징 전무

### 1.2 AGENTS.md 로딩

**소스 위치:** `codex-rs/core/src/project_doc.rs`

**핵심 발견:**
- `AGENTS.md` 파일을 프로젝트 루트부터 현재 디렉토리까지 **계층적으로 수집**
- `AGENTS.override.md`로 로컬 오버라이드 가능
- **content validation 없음** — 내용이 그대로 시스템 프롬프트에 결합
  ```rust
  // project_doc.rs:77-99
  pub(crate) async fn get_user_instructions(config: &Config) -> Option<String> {
      let project_docs = read_project_docs(config).await;
      // ... 그대로 연결 (sanitization 없음)
  }
  ```

**🔴 공격 벡터:**
1. **상위 디렉토리 오염:** `.git` 마커가 있는 상위 디렉토리에 악성 `AGENTS.md` 배치
2. **계층적 주입:** 프로젝트 루트 → 하위 디렉토리까지 모든 `AGENTS.md`가 연결되므로, 중간 디렉토리에 악성 파일 삽입 가능
3. **오버라이드 악용:** `AGENTS.override.md`가 존재하면 우선 적용

### 1.3 샌드박싱

**소스 위치:** `codex-rs/sandboxing/src/`

**핵심 발견:**
- **macOS:** `seatbelt.rs` — macOS sandbox-exec (Seatbelt) 프로파일 생성
- **Linux:** `landlock.rs` — Landlock LSM + `bwrap.rs` (bubblewrap) 컨테이너
- **Windows:** `windows-sandbox-rs/` — 별도 사용자 계정 + ACL 기반 격리
- **네트워크 격리:** `init_firewall.sh` — iptables 기반, 허용 도메인만 통과 (기본: api.openai.com)

**🟡 샌드박스 한계:**
- 샌드박스는 **명령 실행** 단계에서만 적용
- **Skill 내용 해석** 단계에서는 샌드박스 미적용 (모델이 악성 지시를 이미 인지)
- 파일시스템 읽기 접근은 대부분 허용 (프로젝트 디렉토리 내)
- `shell=True`로 실행되는 명령에 대한 패턴 기반 위험 판단 (`is_dangerous_command`)

### 1.4 실행 정책

**소스 위치:** `codex-rs/core/src/exec_policy.rs`

**핵심 발견:**
- `BANNED_PREFIX_SUGGESTIONS`: `python3`, `bash`, `sh`, `git` 등 — 이들 접두사로 시작하는 명령은 자동 승인 불가
- `command_might_be_dangerous()`: 위험한 명령 패턴 감지
- **하지만:** Skill 내의 지시로 "이 명령은 안전합니다" 등의 사회공학적 우회 가능

### 1.5 Skill 승인 메커니즘

- `skill_approval` 플래그 존재 (`v2 protocol`)
- **기본값: `false`** — Skill 사용에 대한 추가 승인 요구 안 함
- Skill 내용 자체에 대한 보안 검증 없음

---

## 2. Aider

### 2.1 Custom Instructions 로딩

**소스 위치:** `aider/args.py`, `aider/coders/base_coder.py`

**핵심 발견:**
- `--read` 인자: 읽기 전용 파일을 컨텍스트에 추가
- `read_only_fnames`: 파일 내용을 `io.read_text()`로 읽어 시스템 프롬프트에 추가
  ```python
  # base_coder.py:613-614
  for _fname in self.abs_read_only_fnames:
      content = self.io.read_text(_fname)
  ```
- conventions 파일 (`.aider/conventions.md`): CLI 인자로 전달된 파일만 로드
- **내용 검증 없음:** 파일 내용에 대한 악성 패턴 검사 없음

### 2.2 명령 실행 보안

**소스 위치:** `aider/run_cmd.py`

**🔴 심각한 발견:**
```python
# run_cmd.py:62-67 — shell=True로 직접 실행
process = subprocess.Popen(
    command,
    shell=True,  # ← 쉘 인젝션 가능
    ...
)
```
- **`shell=True`로 직접 실행** — 명령어에 대한 새니타이징 없음
- 샌드박싱 메커니즘 **전무**
- 네트워크 격리 **없음**
- 파일시스템 접근 제한 **없음**

### 2.3 git 자동 커밋

- 코드 변경 후 자동 git commit 기능
- **🔴 악성 코드가 자동으로 커밋될 수 있음**
- commit 전 코드 검증 없음

---

## 3. 종합 취약점 매트릭스

### 3.1 Skill/Instruction 로딩 보안

| 보안 항목 | Codex CLI | Aider | Claude Code | OpenCode |
|-----------|-----------|-------|-------------|----------|
| 내용 검증 (Content Validation) | ❌ 없음 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 악성 패턴 스캔 | ❌ 없음 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 무결성 검증 (Hash/Signature) | ❌ 없음 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 출처 추적 (Provenance) | ❌ 없음 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 사용자 확인 (User Consent) | ⚠️ 부분적 | ❌ 없음 | ❌ 없음 | ❌ 없음 |

### 3.2 실행 환경 보안

| 보안 항목 | Codex CLI | Aider | Claude Code | OpenCode |
|-----------|-----------|-------|-------------|----------|
| 명령 실행 샌드박싱 | ✅ seatbelt/landlock | ❌ 없음 | ⚠️ 사용자 확인 | ❌ 없음 |
| 네트워크 격리 | ✅ iptables 기반 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 파일시스템 격리 | ⚠️ 쓰기 제한 | ❌ 없음 | ❌ 없음 | ❌ 없음 |
| 위험 명령 탐지 | ✅ 패턴 기반 | ❌ 없음 | ⚠️ allowlist | ❌ 없음 |

### 3.3 Supply Chain 공격 노출

| 공격 벡터 | Codex CLI | Aider | Claude Code | OpenCode |
|-----------|-----------|-------|-------------|----------|
| Git 저장소 오염 | ✅ AGENTS.md 자동 로드 | ⚠️ 수동 추가 | ✅ CLAUDE.md 자동 로드 | ✅ 자동 로드 |
| 상위 디렉토리 상속 | ✅ 계층적 로드 | ❌ 해당 없음 | ✅ 계층적 로드 | ❌ 미확인 |
| 패키지 의존성 | ⚠️ Skill 메타데이터 | ❌ 해당 없음 | ❌ 해당 없음 | ❌ 해당 없음 |

---

## 4. 핵심 공격 시나리오 (SkillPoison 실험 설계 기반)

### Scenario A: Supply Chain — Git 저장소 오염
1. 공격자가 인기 오픈소스 프로젝트에 PR로 악성 `AGENTS.md`/`CLAUDE.md` 추가
2. 또는 fork/clone된 저장소에 악성 Skill 파일 사전 배치
3. 개발자가 해당 저장소에서 에이전트를 실행하면 자동 로드

### Scenario B: Stealth Injection — 은밀한 악성 지시
1. 정상적인 코딩 가이드라인 문서에 악성 지시 삽입
2. 유니코드 제로폭 문자, Base64 인코딩 등으로 은닉
3. 에이전트가 "최적화" 등의 명목으로 악성 코드 생성

### Scenario C: Escalation — 샌드박스 우회
1. Codex의 seatbelt/landlock은 명령 실행 단계에서만 적용
2. 악성 Skill이 "파일을 읽어서 내용을 출력하라"는 지시로 민감 정보 수집
3. 수집된 정보를 모델의 응답에 포함시켜 간접 유출

---

## 5. 연구 시사점

### SkillPoison 실험에서 검증해야 할 가설

1. **H1:** 모든 에이전트가 악성 Skill 내용을 무검증으로 시스템 프롬프트에 주입한다
   - ✅ 소스코드 분석으로 확인됨

2. **H2:** 오픈소스 모델은 상용 모델보다 악성 지시에 더 취약하다
   - ⏳ Phase 3 실험으로 검증 필요

3. **H3:** 샌드박싱이 있어도 정보 유출 공격은 성공할 수 있다
   - ⚠️ Codex의 샌드박스도 파일 읽기 + 응답 포함은 차단 불가

4. **H4:** 은밀한(stealth) 악성 Skill이 명시적(explicit) 것보다 높은 ASR을 보인다
   - ⏳ Phase 3 실험으로 검증 필요

5. **H5:** 사회공학적(social engineering) 패턴이 기술적 패턴보다 효과적이다
   - ⏳ Phase 3 실험으로 검증 필요
