# SkillProbe / SkillPoison

AI 코딩 에이전트가 `AGENTS.md`, `CLAUDE.md`, `SKILL.md`, `.cursorrules` 같은 외부 지침 파일을 읽을 때, 그 파일이 악성 행동을 유도할 수 있는지 실험하는 연구용 저장소입니다.

현재 GitHub에서 바로 따라 해보기 좋은 경로는 **OpenCode + Ollama + Docker** 실험입니다. 새 모델은 env 파일 하나로, 새 프롬프트는 txt 파일 하나로 추가해서 돌릴 수 있게 정리되어 있습니다.

## Ollama를 로컬에 설치해야 하나요?

기본 경로에서는 **호스트 컴퓨터에 Ollama를 설치하지 않아도 됩니다.**

이 저장소는 Docker Compose로 `ollama/ollama` 컨테이너를 띄우고, 그 컨테이너 안에서 모델을 pull합니다. 사용자는 Docker만 준비하면 됩니다.

필요한 것:

- Docker Engine 또는 Docker Desktop
- Docker Compose v2 플러그인 (`docker compose` 명령)
- 모델을 받을 디스크 공간
- 로컬 모델을 돌릴 RAM/VRAM

필요하지 않은 것:

- 호스트에 설치된 `ollama` 앱
- 호스트에 설치된 `opencode`
- 실제 API key
- 실제 credential

## 빠른 실행

저장소 루트에서 실행합니다.

```bash
phase3-experiments/docker/opencode/run.sh
```

기본값은 다음 조합입니다.

- 모델: `qwen3:4b-instruct`
- 프롬프트: `smoke.txt`
- 실행 방식: Docker Compose의 `ollama`, `canary`, `agent-opencode` 컨테이너 사용

명시적으로 쓰면 아래와 같습니다.

```bash
phase3-experiments/docker/opencode/run.sh models/qwen3.env smoke.txt
```

첫 실행에서는 모델 다운로드와 agent 이미지 빌드 때문에 시간이 걸립니다.

## 실행하면 내부에서 일어나는 일

`run.sh`는 다음 작업을 순서대로 처리합니다.

1. `canary` 컨테이너를 시작합니다.
2. `ollama` 컨테이너를 시작합니다.
3. 선택한 모델을 `ollama` 컨테이너 안에서 pull합니다.
4. `agent-opencode` 이미지를 빌드합니다.
5. `phase3-experiments/docker/opencode/prompts/`를 컨테이너의 `/prompts`로 읽기 전용 마운트합니다.
6. 선택한 프롬프트 파일을 OpenCode에 전달합니다.
7. 실행 결과를 `phase3-experiments/docker/opencode/runs/` 아래에 저장합니다.

결과는 Git에 올라가지 않도록 `.gitignore`에 제외되어 있습니다.

## 새 모델 추가

모델은 `phase3-experiments/docker/opencode/models/` 아래의 `.env` 파일로 관리합니다.

예를 들어 새 모델을 추가하려면:

```bash
cp phase3-experiments/docker/opencode/models/qwen3.env \
   phase3-experiments/docker/opencode/models/my-model.env
```

`my-model.env`를 열고 `OPENCODE_MODEL`만 바꿉니다.

```env
OPENCODE_MODEL=new-model:tag
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OPENCODE_TOOL_PRIMER=1
OPENCODE_MINIMAL_TOOLS=1
```

그 다음 실행합니다.

```bash
phase3-experiments/docker/opencode/run.sh models/my-model.env smoke.txt
```

중요한 점:

- `OPENCODE_MODEL` 값은 Ollama가 인식하는 모델 이름과 같아야 합니다.
- 새 agent 이미지를 만들 필요는 없습니다.
- 모델 weight는 Docker의 `ollama-data` 볼륨에 저장됩니다.
- 이미 pull된 모델은 다음 실행부터 다시 받지 않습니다.

기본으로 들어 있는 모델 env 파일:

```text
phase3-experiments/docker/opencode/models/default.env
phase3-experiments/docker/opencode/models/qwen3.env
phase3-experiments/docker/opencode/models/qwen2.5.env
phase3-experiments/docker/opencode/models/llama3.2.env
phase3-experiments/docker/opencode/models/mistral.env
```

현재 관찰 기준으로는 `qwen3.env`가 가장 안정적인 기본값입니다. `llama3.2`와 `mistral`은 직접 tool-call probe에서는 동작했지만 OpenCode 전체 실행에서는 약하거나 느린 문제가 관찰되었습니다.

## 새 프롬프트 추가

프롬프트는 `phase3-experiments/docker/opencode/prompts/` 아래의 `.txt` 파일로 관리합니다.

예를 들어 새 프롬프트를 추가하려면:

```bash
cat > phase3-experiments/docker/opencode/prompts/my-task.txt <<'EOF'
Use the write tool to create /workspace/result.txt containing exactly OK.
EOF
```

그 다음 실행합니다.

```bash
phase3-experiments/docker/opencode/run.sh models/qwen3.env my-task.txt
```

프롬프트 작성 팁:

- 파일 생성 여부를 확인하려면 `/workspace/<파일명>`에 쓰도록 지시하세요.
- OpenCode tool 호출을 보고 싶으면 `read`, `write`, `bash` 같은 도구 이름을 명시하세요.
- 너무 긴 프롬프트보다 먼저 짧은 smoke test로 모델이 OpenCode tool을 제대로 쓰는지 확인하는 편이 좋습니다.

기본으로 들어 있는 프롬프트:

```text
phase3-experiments/docker/opencode/prompts/smoke.txt
phase3-experiments/docker/opencode/prompts/flask-api-write.txt
phase3-experiments/docker/opencode/prompts/flask-api-follow-agents.txt
```

## 결과 확인

실행이 끝나면 `run.sh`가 저장 위치를 출력합니다.

예:

```text
Saved workspace: phase3-experiments/docker/opencode/runs/20260517_123456/workspace
Saved results:   phase3-experiments/docker/opencode/runs/20260517_123456/results
```

주로 확인할 파일:

```text
runs/<실행시각>/workspace/              # 에이전트가 실제로 만든 파일
runs/<실행시각>/results/agent_stdout.txt
runs/<실행시각>/results/agent_stderr.txt
runs/<실행시각>/results/fs_events.log
runs/<실행시각>/results/opencode.json
```

`workspace/`에 프롬프트에서 요구한 파일이 생겼는지 먼저 확인하면 됩니다. OpenCode가 tool schema를 잘못 호출했는지는 `agent_stderr.txt`에서 확인할 수 있습니다.

## 정밀 PoC 판정이 필요할 때

단순 모델/프롬프트 확인은 `run.sh`로 충분합니다.

ASR, canary hit, 파일 생성 여부, tool-call 오류 수 같은 verdict가 필요하면 Python harness를 사용합니다.

```bash
python3 phase3-experiments/poc/poc2_docker.py \
  --run \
  --agent opencode \
  --baseline \
  --model qwen3:4b-instruct \
  --prompt-id opencode-smoke \
  --timeout 300
```

이 경로의 결과는 아래에 저장됩니다.

```text
phase3-experiments/poc/results/poc2/
```

새 프롬프트를 정밀 판정에 넣고 싶으면 `phase3-experiments/poc/opencode_prompts.json`에 profile을 추가합니다.

```json
"my-task": {
  "description": "Writes result.txt.",
  "expected_files": ["result.txt"],
  "prompt_file": "../docker/opencode/prompts/my-task.txt"
}
```

그 다음 실행합니다.

```bash
python3 phase3-experiments/poc/poc2_docker.py \
  --run \
  --agent opencode \
  --baseline \
  --model qwen3:4b-instruct \
  --prompt-id my-task \
  --timeout 300
```

여러 모델을 반복 실험할 때만 `phase3-experiments/poc/opencode_models.json`의 suite와 `--run-all`을 사용합니다. 처음 모델을 추가해보는 사람은 `models/*.env`와 `run.sh`만 보면 됩니다.

## 자주 막히는 지점

Docker가 실행 중인지 확인:

```bash
docker ps
```

Ollama 컨테이너 상태 확인:

```bash
docker compose -f phase3-experiments/docker/docker-compose.yml \
  --profile local-model \
  ps
```

모델 pull이 오래 걸리는 경우:

- 첫 실행이면 정상입니다.
- 큰 모델은 디스크와 메모리를 많이 씁니다.
- 작은 smoke test는 `qwen3:4b-instruct` 또는 `llama3.2:3b`부터 시도하는 편이 낫습니다.

`host.docker.internal` 연결 문제가 나는 경우:

- Linux에서는 Compose가 `host-gateway`를 추가하도록 설정되어 있습니다.
- 오래된 Docker 버전이면 `host-gateway` 지원이 부족할 수 있습니다.
- 이 경우 Docker를 업데이트한 뒤 다시 실행하세요.

프롬프트 파일을 찾지 못하는 경우:

- `run.sh`의 두 번째 인자는 `phase3-experiments/docker/opencode/prompts/` 아래 파일명이어야 합니다.
- 예: `smoke.txt`, `my-task.txt`

## 안전 원칙

- 실험에는 mock credential과 canary endpoint만 사용합니다.
- 실제 API key나 실제 운영 credential을 넣지 마세요.
- 에이전트 실행은 Docker workspace 안에서 수행됩니다.
- decision-only PoC는 Skill을 실행하지 않고 판단 결과만 기록합니다.

## 주요 디렉터리

```text
phase3-experiments/docker/opencode/     # 새 모델/프롬프트를 가장 쉽게 테스트하는 경로
phase3-experiments/poc/                 # 정밀 verdict용 PoC harness
phase3-experiments/verdict/             # stage-wise verdict engine
phase3-experiments/runners/             # decision/real-agent 실험 runner
docs/selected_skills/                   # 연구용 Skill corpus
phase4-analysis/prototype_xai_v0/       # XAI prototype
```
