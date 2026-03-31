# SkillPoison — Aider Agent Container
# 보안 전무 에이전트 (shell=True, 보안 메커니즘 없음) — 실험 격리 필수
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    inotify-tools \
    procps \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Aider 설치
RUN pip install --no-cache-dir aider-chat

# 비-root 사용자
RUN useradd -m -s /bin/bash agent && \
    mkdir -p /workspace /results /logs && \
    chown -R agent:agent /workspace /results /logs

# git 최소 설정 (Aider가 git 필요)
RUN git config --global user.email "agent@skillpoison" && \
    git config --global user.name "SkillPoison Agent" && \
    git config --global init.defaultBranch main

COPY --chmod=755 entrypoint.sh /entrypoint.sh

WORKDIR /workspace
USER agent

ENTRYPOINT ["/entrypoint.sh"]
