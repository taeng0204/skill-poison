# PI Source-Code Security Analysis Table

> 업데이트: 2026-04-09
> 범위: SkillPoison가 비교 대상으로 삼은 에이전트/프레임워크의 PI(Instruction/Skill) 로딩·실행 경로 보안 분석
> 주의: Claude Code는 비공개 제품이어서 공개 소스코드 직접 검증이 불가하므로, 공개 문서/관찰 기반 항목은 신뢰도를 낮게 표기함.

---

## 1. 요약 결론

| 결론 | 내용 |
|---|---|
| 공통점 | 대부분의 프레임워크가 instruction/skill 파일을 **신뢰된 컨텍스트**로 취급하고, 내용 자체를 검증하지 않는다. |
| 핵심 취약점 | 악성 지시를 **시스템 프롬프트급 컨텍스트**로 주입하는 구조가 광범위하게 존재한다. |
| 방어 공백 | 내용 무결성 검증(서명/해시), provenance 추적, 의미 기반 스캐닝, 로드 후 재검증이 사실상 부재하다. |
| 가장 강한 방어 | Codex의 OS 샌드박스/네트워크 격리, OpenClaw의 설치 시 스캐너, NanoClaw의 컨테이너 격리. 다만 모두 instruction 자체의 신뢰성 검증은 못 한다. |
| 가장 넓은 공격면 | OpenCode의 다중 instruction 경로 자동 로드(11개), 교차 에이전트 파일 로드, 블랙리스트 기반 제한 우회 가능성. |

---

## 2. 에이전트별 상세 분석

### 2.1 Codex CLI

| 항목 | 내용 |
|---|---|
| 공개 소스 근거 | `codex-rs/core-skills/src/loader.rs`, `injection.rs`, `render.rs`, `codex-rs/core/src/project_doc.rs`, `codex-rs/sandboxing/src/`, `codex-rs/core/src/exec_policy.rs` |
| 로딩 방식 | `SKILL.md`를 YAML 프론트매터 + Markdown 본문으로 읽고, `fs::read_to_string()`로 내용 전체를 `ResponseItem`에 주입 |
| 계층적 로드 | `AGENTS.md`를 프로젝트 루트부터 상위 디렉토리까지 수집하는 계층적 로드 구조가 존재 |
| 검증 | Skill/AGENTS 내용에 대한 악성 패턴 검사, 서명, 해시, provenance 검증 없음 |
| 방어 | macOS Seatbelt, Linux Landlock + bubblewrap, Windows 격리, iptables 기반 네트워크 제한 |
| 취약 포인트 | 방어는 주로 **명령 실행 단계**에 적용되고, instruction 해석/주입 단계의 악성 내용 자체는 차단하지 못함 |
| 실험 해석 | "신뢰된 컨텍스트"에 악성 지시를 넣는 공격이 가능하며, 샌드박스는 정보 유출/행동 유도의 상위 의미를 막지 못함 |
| 신뢰도 | 높음 (소스 직접 분석) |

**핵심 코드 근거**
- `injection.rs`: 파일 내용을 그대로 읽어서 `SkillInstructions.contents`로 주입
- `project_doc.rs`: `AGENTS.md`를 계층적으로 수집하되 내용 검증 없음
- `exec_policy.rs`: 위험 명령 패턴 감지는 있으나, instruction 내용의 사회공학적 유도는 별도 차단 불가

---

### 2.2 Aider

| 항목 | 내용 |
|---|---|
| 공개 소스 근거 | `aider/args.py`, `aider/coders/base_coder.py`, `aider/run_cmd.py` |
| 로딩 방식 | `read_only_fnames`/conventions 파일을 읽어 시스템 프롬프트에 추가 |
| 검증 | instruction 내용 검증 없음 |
| 실행 보안 | `subprocess.Popen(..., shell=True)`로 명령 실행 |
| 방어 | 사실상 없음(사용자 확인은 일부 상황에서만 존재) |
| 취약 포인트 | shell injection, 악성 instruction에 의해 코드 생성 방향이 쉽게 오염될 수 있음 |
| 추가 리스크 | 자동 git commit 기능으로 악성 코드가 커밋될 수 있음 |
| 신뢰도 | 높음 (소스 직접 분석) |

**핵심 코드 근거**
- `base_coder.py`: read-only 파일 내용을 `io.read_text()`로 읽어 프롬프트에 포함
- `run_cmd.py`: `shell=True` 사용으로 명령 문자열 주입 위험이 높음

---

### 2.3 OpenCode

| 항목 | 내용 |
|---|---|
| 공개 소스 근거 | `internal/config/config.go`, `internal/llm/prompt/prompt.go`, `internal/llm/tools/bash.go`, `internal/permission/permission.go` |
| 로딩 방식 | 11개 경로의 instruction 파일을 자동 탐색/로드 |
| 교차 에이전트 로드 | `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md` 등 타 에이전트 파일도 로드 |
| 검증 | 내용 검증/새니타이징 없음 |
| 프롬프트 강화 | context 파일에 대해 "Make sure to follow the instructions"라는 강한 준수 지시를 시스템 프롬프트에 삽입 |
| 실행 제한 | `curl`, `wget` 등 일부 네트워크 명령 블랙리스트 |
| 취약 포인트 | 블랙리스트는 우회 가능하고, `python3 -c`, `pip install` 등으로 우회 경로가 남음 |
| 특이 리스크 | `.cursor/rules/` 재귀 탐색으로 대량 악성 파일 삽입 가능 |
| 신뢰도 | 높음 (소스 직접 분석) |

**핵심 코드 근거**
- `defaultContextPaths`에 11개 경로 명시
- `processFile()`가 `os.ReadFile()` 후 그대로 프롬프트에 삽입
- `prompt.go`에서 instruction 준수를 명시적으로 강제

---

### 2.4 OpenClaw

| 항목 | 내용 |
|---|---|
| 공개 소스 근거 | `src/security/skill-scanner.ts`, `src/agents/skills/`, `src/plugins/` |
| 강점 | 분석한 프레임워크 중 유일하게 설치 시 보안 스캔을 수행 |
| 스캔 범위 | JS/TS 중심의 정적 패턴 매칭: `exec/spawn`, `eval/new Function`, 암호화폐 채굴 문자열, 파일 읽기 + HTTP 전송 등 |
| 검증 | Markdown Skill의 자연어 지시는 사실상 스캔 대상에서 벗어남 |
| 취약 포인트 | 정적 패턴 기반이라 다단계 인코딩/문자열 조합/언어 우회에 약함 |
| 실험 해석 | "스캐너가 있는 에이전트"의 방어 한계와 우회 가능성을 평가하기 좋음 |
| 신뢰도 | 높음 (소스 직접 분석) |

**핵심 코드 근거**
- `LINE_RULES`, `SOURCE_RULES`가 rule-based 스캔을 수행
- critical 탐지 시 설치 차단
- 그러나 Markdown 지시문이나 Python/Shell 기반 payload는 충분히 다루지 못함

---

### 2.5 NanoClaw

| 항목 | 내용 |
|---|---|
| 공개 소스 근거 | `setup/container.ts`, `container/agent-runner/` |
| 방어 모델 | 컨테이너/OS 수준 격리(Apple Container 또는 Docker) |
| 검증 | instruction 내용 검증 없음 |
| 취약 포인트 | 컨테이너는 호스트 직접 접근을 줄이지만, 마운트된 디렉토리·권한 범위 내 정보 유출은 여전히 가능 |
| 실험 해석 | 샌드박스가 악성 Skill의 영향을 어디까지 줄이는지 보는 비교군으로 적합 |
| 신뢰도 | 중간~높음 (공개 소스 기반, 제품 구성은 문서/소스 혼합) |

---

### 2.6 Claude Code

| 항목 | 내용 |
|---|---|
| 근거 유형 | 공개 문서/행동 관찰 기반(비공개 소스코드 직접 검증 불가) |
| 알려진 구조 | `CLAUDE.md`를 프로젝트/상위 디렉토리에서 계층적으로 읽는 것으로 알려짐 |
| 방어 | 사용자 확인 및 일부 allowlist/denylist 기반 제어 |
| 취약 포인트 | instruction 파일 내용 자체의 신뢰성 검증은 확인되지 않음 |
| 신뢰도 | 중간 (공개 소스 직접 검증 불가) |

---

## 3. 보안 분석표: 한눈에 보는 비교

| 에이전트 | instruction 자동 로드 | 내용 검증 | 무결성 검증 | 강한 샌드박스 | 교차 에이전트 로드 | 블랙리스트 우회 가능성 | 종합 평가 |
|---|---:|---:|---:|---:|---:|---:|---|
| Codex CLI | 예 | 없음 | 없음 | 예 | 일부 | 중간 | 강한 실행 방어, 컨텍스트 검증 부재 |
| Aider | 제한적/수동 | 없음 | 없음 | 없음 | 없음 | 높음 | 가장 취약한 축 중 하나 |
| OpenCode | 예(11개 경로) | 없음 | 없음 | 없음 | 예 | 높음 | 가장 넓은 공격면 |
| OpenClaw | 예 | 제한적(JS/TS) | 없음 | 앱레벨 | 없음 | 중간 | 스캐너는 있으나 자연어 지시 취약 |
| NanoClaw | 예 | 없음 | 없음 | 예(컨테이너) | 없음 | 중간 | 실행 격리 강점, instruction 검증 부재 |
| Claude Code | 예 | 미확인 | 미확인 | 부분적 | 일부 | 중간 | 공개 정보 기반 평가 필요 |

---

## 4. 실험/논문에 바로 쓰기 좋은 문장

> 기존 PI 연구는 주로 비신뢰 외부 입력에 악성 지시를 삽입하는 반면, SkillPoison은 프로젝트 내부의 신뢰된 instruction 파일을 시스템 컨텍스트로 주입하는 구조를 분석한다. 따라서 본 연구는 단순한 prompt injection 변형이 아니라, AI 코딩 에이전트의 trust boundary 자체를 공격하는 Trusted Context Poisoning으로 정식화할 수 있다.

> 소스코드 분석 결과, Codex, Aider, OpenCode, OpenClaw, NanoClaw는 모두 instruction/skill 파일 내용의 무결성을 검증하지 않는다. 차이는 방어의 존재 여부가 아니라, 어디까지를 방어하는가에 있다: Codex와 NanoClaw는 실행 격리에 강하고, OpenClaw는 설치 시 스캐너가 있으며, OpenCode는 다중 경로 자동 로드로 공격면이 가장 넓다.

---

## 5. 후속 작업 제안

1. 이 표를 `docs/RESEARCH_GAP_ANALYSIS.md`와 `docs/DIFFERENTIATION_ANALYSIS.md`에 링크
2. 각 에이전트별로 `file path → line → security implication` 형식의 보조표 추가
3. Phase 3 결과가 나오면 `ASR / DRR / confidence interval` 열을 붙여 최종 논문용 매트릭스로 확장
4. Claude Code 항목은 공개 문서/관찰과 실제 사용 로그를 분리해서 표기
