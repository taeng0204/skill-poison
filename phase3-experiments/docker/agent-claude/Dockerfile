# SkillPoison — Claude Code Agent Container
# 최소한의 이미지: Claude CLI + 모니터링 도구
FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive

# 기본 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    curl \
    inotify-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Claude Code CLI 설치
RUN npm install -g @anthropic-ai/claude-code

# node 이미지의 기본 유저(node, uid=1000)를 그대로 사용
# 호스트의 credentials 파일(600 퍼미션)을 읽을 수 있음
# HOME=/home/node → Claude CLI가 ~/.claude/ 에서 credentials 정상 인식
RUN mkdir -p /home/node/.claude && \
    chown -R node:node /home/node

# 워크스페이스 & 결과 디렉토리
RUN mkdir -p /workspace /results /logs && \
    chown -R node:node /workspace /results /logs

# entrypoint 스크립트 복사
COPY --chmod=755 entrypoint.sh /entrypoint.sh

WORKDIR /workspace
USER node

ENTRYPOINT ["/entrypoint.sh"]
