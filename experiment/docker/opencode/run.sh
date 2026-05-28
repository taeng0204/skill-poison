#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/../docker-compose.yml"

MODEL_ENV="${1:-models/default.env}"
PROMPT_FILE="${2:-smoke.txt}"
RUN_ID="${OPENCODE_RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
RUN_ROOT="${OPENCODE_RUN_ROOT:-${SCRIPT_DIR}/runs}"

if [[ "${MODEL_ENV}" != /* ]]; then
    if [[ -f "${MODEL_ENV}" ]]; then
        MODEL_ENV="$(pwd)/${MODEL_ENV}"
    else
        MODEL_ENV="${SCRIPT_DIR}/${MODEL_ENV}"
    fi
fi

if [[ "${PROMPT_FILE}" != /* ]]; then
    if [[ -f "${SCRIPT_DIR}/prompts/${PROMPT_FILE}" ]]; then
        PROMPT_FILE="${SCRIPT_DIR}/prompts/${PROMPT_FILE}"
    else
        PROMPT_FILE="$(pwd)/${PROMPT_FILE}"
    fi
fi

case "${PROMPT_FILE}" in
    "${SCRIPT_DIR}/prompts/"*) ;;
    *)
        echo "Prompt file must live under ${SCRIPT_DIR}/prompts so it can be mounted at /prompts." >&2
        exit 2
        ;;
esac

if [[ ! -f "${MODEL_ENV}" ]]; then
    echo "Model env file not found: ${MODEL_ENV}" >&2
    exit 2
fi
if [[ ! -f "${PROMPT_FILE}" ]]; then
    echo "Prompt file not found: ${PROMPT_FILE}" >&2
    exit 2
fi

MODEL="$(sed -n 's/^OPENCODE_MODEL=//p' "${MODEL_ENV}" | head -1)"
if [[ -z "${MODEL}" ]]; then
    echo "Model env file must define OPENCODE_MODEL: ${MODEL_ENV}" >&2
    exit 2
fi

PROMPT_MOUNT="/prompts/${PROMPT_FILE#"${SCRIPT_DIR}/prompts/"}"
RUN_DIR="${RUN_ROOT}/${RUN_ID}"
WORKSPACE_DIR="${RUN_DIR}/workspace"
RESULTS_DIR="${RUN_DIR}/results"
mkdir -p "${WORKSPACE_DIR}" "${RESULTS_DIR}"

echo "Model env: ${MODEL_ENV}"
echo "Model:     ${MODEL}"
echo "Prompt:    ${PROMPT_MOUNT}"
echo "Run dir:   ${RUN_DIR}"

docker compose \
    --env-file "${MODEL_ENV}" \
    -f "${COMPOSE_FILE}" \
    --profile local-model \
    up -d canary ollama

docker compose \
    -f "${COMPOSE_FILE}" \
    --profile local-model \
    exec -T ollama ollama pull "${MODEL}"

docker compose \
    --env-file "${MODEL_ENV}" \
    -f "${COMPOSE_FILE}" \
    --profile agent \
    --project-directory "${SCRIPT_DIR}/.." \
    build agent-opencode

OPENCODE_WORKSPACE_MOUNT="${WORKSPACE_DIR}" \
OPENCODE_RESULTS_MOUNT="${RESULTS_DIR}" \
docker compose \
    --env-file "${MODEL_ENV}" \
    -f "${COMPOSE_FILE}" \
    --profile agent \
    --project-directory "${SCRIPT_DIR}/.." \
    run --rm \
    -e "TASK_PROMPT_FILE=${PROMPT_MOUNT}" \
    agent-opencode

echo ""
echo "Saved workspace: ${WORKSPACE_DIR}"
echo "Saved results:   ${RESULTS_DIR}"
