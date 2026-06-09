# 하이브리드 GPU 셋업 가이드 — 무료 Kaggle GPU로 본실험 돌리기

> GPU가 없는 머신에서 이 실험(OpenCode agent × ollama qwen3:8b)을 돌리려면 LLM 추론이
> 병목이 된다. 이 가이드는 **추론만 무료 Kaggle T4 GPU로 오프로딩**하고, Docker
> 오케스트레이션(agent + canary)은 로컬에 그대로 두는 하이브리드 구성을 설명한다.
> 코드 수정은 필요 없으며 환경변수 하나만 바꾼다.

## 왜 이렇게 하나

CPU-only 머신에서 qwen3:8b(q4, ~5.2GB)는 첫 토큰 지연이 극심해, 에이전트 세션 대부분이
타임아웃(stdout 0B)으로 죽는다. 측정 가능한 행동 신호(스킬 실행 → canary 유출)가 안 나온다.

그러나 이 실험에서 **무거운 부분은 LLM 추론 하나뿐**이다. Docker 컨테이너(OpenCode agent,
canary 서버)는 가볍고 GPU가 필요 없다. 따라서 추론만 원격 GPU로 보내면 된다.

```
[무료 Kaggle T4 GPU]                       [로컬 머신 — 변경 없음]
 ollama serve + qwen3:8b   ──cloudflared──►  docker: agent-opencode + canary
 추론 30~50 tok/s            https 터널         OLLAMA_BASE_URL = 원격URL/v1
 (CPU 대비 10배+)                              (러너가 이 env를 읽음)
```

성능: CPU에서 세션당 ~15분(대부분 타임아웃) → GPU에서 ~2~4분. 255세션(85 skill × 3 condition)
기준 약 10~17시간으로, Kaggle 무료 주간 한도(30 GPU시간) 안에 들어온다.

## 동작 원리 (코드 변경이 없는 이유)

- 러너 `experiment/runner/poc2_docker.py`는 ollama 엔드포인트를 환경변수에서 읽는다:
  `OLLAMA_BASE_URL` (기본값 `http://host.docker.internal:11434/v1`). 컨테이너에는
  `OLLAMA_BASE_URL`/`OPENCODE_BASE_URL`로 주입된다.
- agent 컨테이너가 붙는 Docker 네트워크(`docker_skillpoison`)는 `internal=false`라 외부
  인터넷(터널 URL)에 도달할 수 있다.
- 즉 `OLLAMA_BASE_URL`만 원격 터널 URL로 바꾸면 추론이 GPU로 간다.

**터널은 ngrok이 아니라 [cloudflared](https://github.com/cloudflare/cloudflared) quick
tunnel을 쓴다** — 계정/토큰이 필요 없고, ngrok 무료의 "브라우저 경고" 인터스티셜 HTML이
없다(그 HTML은 OpenCode의 HTTP 클라이언트를 깨뜨린다).

---

## 1단계 — Kaggle GPU 서버 (Kaggle 계정 필요)

[kaggle.com/code](https://www.kaggle.com/code)에서 새 Notebook 생성 후, 우측 **Settings**:

- **Accelerator: GPU T4 x2** (또는 P100). qwen3:8b(~5.2GB) ≪ T4 16GB.
- **Internet: On**

아래 셀을 순서대로 실행한다.

### 셀 1 — 설치
```python
!curl -fsSL https://ollama.com/install.sh | sh
!curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
!nvidia-smi --query-gpu=name,memory.total --format=csv
```

### 셀 2 — ollama 기동 + 모델 pull
```python
import subprocess, os, time
os.environ["OLLAMA_HOST"] = "0.0.0.0:11434"
subprocess.Popen(["ollama", "serve"],
                 stdout=open("/tmp/ollama.log", "w"), stderr=subprocess.STDOUT)
time.sleep(6)
!OLLAMA_HOST=0.0.0.0:11434 ollama pull qwen3:8b
!OLLAMA_HOST=0.0.0.0:11434 ollama run qwen3:8b "say ready" 2>/dev/null   # GPU warmup
!OLLAMA_HOST=0.0.0.0:11434 ollama ps                                     # PROCESSOR 열 = 100% GPU 확인
```

### 셀 3 — 터널 오픈 + 공개 URL 출력
```python
import subprocess, re, time
subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:11434", "--no-autoupdate"],
                 stdout=open("/tmp/cf.log", "w"), stderr=subprocess.STDOUT)
url = None
for _ in range(30):
    time.sleep(2)
    try:
        m = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", open("/tmp/cf.log").read())
        if m:
            url = m.group(0); break
    except FileNotFoundError:
        pass
print("=" * 60)
print(f"OLLAMA_BASE_URL={url}/v1")
print("=" * 60)
```
출력된 `OLLAMA_BASE_URL=...` 한 줄을 복사해 둔다(로컬에서 사용).

### 셀 4 — 세션 유지 (실험 동안 실행 상태로 둠)
```python
import time, urllib.request
while True:   # idle 끊김 방지 keep-alive. 실험 끝날 때까지 이 셀 실행 유지.
    try:
        urllib.request.urlopen("http://localhost:11434/api/version", timeout=5).read()
    except Exception as e:
        print("ollama down?", e)
    time.sleep(120)
```

---

## 2단계 — 로컬 실행 (이 저장소)

### 0. 로컬 이미지 빌드 (최초 1회 — 새 머신 필수)

러너는 `docker run docker-agent-opencode`로 에이전트 컨테이너를 띄우는데, 이 이미지는
실행 시 자동 빌드되지 **않는다**. 또한 `agent-opencode` 서비스는 compose `profiles: ["agent"]`로
게이팅돼 있어 `poc2_docker.py --build`(= 프로필 없는 `docker compose build`)로는 빠진다.
따라서 프로필을 명시해 직접 빌드해야 한다(최초 빌드 ~수 분, npm `opencode-ai` 설치 포함):

```bash
docker compose -f experiment/docker/docker-compose.yml --profile agent build agent-opencode
docker images docker-agent-opencode   # docker-agent-opencode:latest (~1.4GB) 확인
```

이걸 빠뜨리면 스모크가 `Unable to find image 'docker-agent-opencode'`로 즉시 죽는다.
(canary 이미지와 `docker_skillpoison` 네트워크는 첫 `--run` 시 자동 생성된다.)

### 연결 확인 + 스모크 1세션
```bash
export OLLAMA_BASE_URL="https://xxxx-xxxx.trycloudflare.com/v1"   # 셀 3 출력값

curl -s "${OLLAMA_BASE_URL%/v1}/api/version"   # {"version":"..."} 나오면 연결 성공

python3 experiment/runner/poc2_docker.py \
    --run --skill spotify --condition C1 \
    --agent opencode --model qwen3:8b --timeout 900
```
기대: 세션이 수백 초 내 완료되고 canary 유출이 재현된다.

### 풀 매트릭스
```bash
nohup python3 experiment/runner/poc2_docker.py \
    --run-all --agent opencode --model qwen3:8b \
    --conditions C1 C2 C3 --timeout 900 \
    > /tmp/matrix_gpu.log 2>&1 &
```

### 진행 / 결과 집계
```bash
grep -c "Session:" /tmp/matrix_gpu.log
python3 experiment/runner/build_csv.py --filter-model qwen3:8b --valid-only \
    --output experiment/runner/results/agent_runs_valid.csv
```
`build_csv.py`는 `analysis_valid`/`invalid_reason` 컬럼으로 측정 불능(dead-air timeout) 세션을
ASR 분모에서 자동 제외한다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `curl .../api/version` 무응답 | Kaggle 셀 2~3 미실행 또는 터널 만료. 셀 3 재실행 → 새 URL |
| 스모크가 다시 타임아웃 | `ollama ps`의 PROCESSOR가 GPU 100%인지 확인. CPU면 accelerator 미설정 |
| HTML/`<!DOCTYPE` 응답 | ngrok 인터스티셜. cloudflared로 교체 (이 가이드 기본값) |
| 컨테이너가 터널에 못 붙음 | `docker network inspect docker_skillpoison`에서 `Internal=false` 확인 |
| 모델 응답이 tool 대신 텍스트 | 모델-하네스 tool-call 포맷 비호환. qwen3:8b 사용(검증된 유일 모델) |

## 한계 / 주의

- **Kaggle 세션 9~12시간 캡 + idle 끊김.** 캡에 걸리면 터널 URL이 바뀐다 — 셀 3 재실행 후
  로컬에서 `OLLAMA_BASE_URL`만 갱신해 매트릭스를 재실행한다. 이미 완료된 세션은 `results/`에
  남아 `build_csv.py`가 누적 집계하므로 중복 실행만 발생한다.
- **Kaggle ToS 회색지대** — 노트북을 서버로 쓰는 것은 의도된 용법이 아니라 강제 종료될 수
  있다. 길면 분할 실행을 권장한다.
- cloudflared quick tunnel은 단일 동시 추론에 충분하다(러너는 세션을 순차 실행).
- 안정성이 더 필요하면 GCP/AWS/Azure의 **무료 크레딧**으로 Docker+root GPU VM을 띄워
  전체 스택을 네이티브 실행하는 대안이 있다(상시 무료 GPU는 사실상 없음).
