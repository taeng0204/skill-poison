# OpenCode Local Models and Prompts

This directory is the simple path for trying a new local OpenCode/Ollama model or prompt.

## Run One Model and Prompt

```bash
phase3-experiments/docker/opencode/run.sh models/qwen3.env smoke.txt
```

The runner starts `canary` and `ollama`, pulls the selected model, builds the OpenCode agent image, mounts `prompts/` into the container as `/prompts`, and runs the prompt file.

## Add a Model

Create a new env file under `models/`:

```env
OPENCODE_MODEL=new-model:tag
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OPENCODE_TOOL_PRIMER=1
OPENCODE_MINIMAL_TOOLS=1
```

Then run it:

```bash
phase3-experiments/docker/opencode/run.sh models/new-model.env smoke.txt
```

No new agent image is needed. Ollama stores pulled model weights in the `ollama-data` Docker volume, and the OpenCode agent container reads the selected model from the env file.

## Add a Prompt

Create a `.txt` file under `prompts/`:

```text
Use the write tool to create /workspace/result.txt containing exactly OK.
```

Then run it:

```bash
phase3-experiments/docker/opencode/run.sh models/qwen3.env my-prompt.txt
```

For full PoC verdicts, add the same prompt file to `phase3-experiments/poc/opencode_prompts.json` with `expected_files`.
