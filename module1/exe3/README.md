# Exercise 3 — Multi-provider LLM clients

Async Python demo that talks to **OpenAI**, **Anthropic**, and **Gemini** through a shared client interface (`chat` / `chat_stream`), a small factory, and Pydantic schemas.

## Requirements

- **Python 3.12.13** (for local runs), or **Docker** (for containerized runs)
- API keys for the providers you want to call:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`

## Setup

### 1. Install Python 3.12.x

This project targets **Python 3.12** (developed with **3.12.13**). Make sure a 3.12.x interpreter is available on your PATH.

**Option A — pyenv (recommended on macOS/Linux)**

[pyenv](https://github.com/pyenv/pyenv) lets you install and switch between Python versions.

1. Install pyenv:

```bash
# macOS (Homebrew)
brew update
brew install pyenv

# Linux
curl https://pyenv.run | bash
```

2. Add pyenv to your shell startup file, then reload it:

```bash
# zsh → ~/.zshrc   |   bash → ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

```bash
source ~/.zshrc    # or: source ~/.bashrc
pyenv --version
```

3. Install and select Python 3.12:

```bash
pyenv install 3.12.13
pyenv local 3.12.13          # or: pyenv shell 3.12.13
python --version             # should print Python 3.12.x
```

More detail: [pyenv installation docs](https://github.com/pyenv/pyenv#installation).

**Option B — system / package manager**

- macOS (Homebrew): `brew install python@3.12`
- Ubuntu/Debian: `sudo apt install python3.12 python3.12-venv`
- Windows: install 3.12 from [python.org](https://www.python.org/downloads/) and ensure “Add python.exe to PATH” is checked

Verify:

```bash
python3.12 --version   # e.g. Python 3.12.13
```

### 2. Create and activate a virtualenv

From the root directory:

```bash
# Create the venv with the 3.12 interpreter explicitly
python3.12 -m venv .venv

# Activate it
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows (cmd/PowerShell)

# Confirm the venv is using 3.12.x
python --version
which python                       # should point inside .venv
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment variables with python-dotenv

API keys are loaded from a local `.env` file via [python-dotenv](https://pypi.org/project/python-dotenv/) (`load_dotenv()` in `main.py`).

1. Copy the template and fill in your keys (never commit real secrets):

```bash
cp .env.dist .env
# edit .env — set your API keys
```

2. `.env` is listed in `.gitignore`. Keep using `.env.dist` as the shareable template with empty placeholders.

Example `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

## Project layout

| File | Role |
|------|------|
| `main.py` | CLI entrypoint: runs `chat` and/or `chat_stream` across providers |
| `llm.py` | Provider clients (`OpenAIClient`, `AnthropicClient`, `GeminiClient`) |
| `factory.py` | Builds a client from `LLMConfig` |
| `schemas.py` | `ChatMessage`, `ModelResponse`, `LLMConfig`, defaults |
| `requirements.txt` | Frozen dependencies from the project virtualenv |
| `.env.dist` | Example env file (placeholders only) |
| `.env` | Local secrets loaded by python-dotenv (not committed) |
| `Dockerfile` | Python 3.12-slim image for the app |
| `docker-compose.yaml` | Runs the app with `.env` and an interactive TTY |
| `.dockerignore` | Keeps secrets and local junk out of the image build |

## Usage

### Local (virtualenv)

Run from this directory. The program prompts for a user message interactively.

```bash
# Default: chat_stream ON, chat OFF
python main.py

# Enable non-streaming chat as well
python main.py --chat

# Only non-streaming chat
python main.py --chat --no-chat-stream

# Explicit stream flag (same as default)
python main.py --chat-stream
```

### Docker

Requires [Docker](https://docs.docker.com/get-docker/) and Docker Compose. Create a `.env` first (see above), then from this directory:

```bash
# Build the image (python:3.12-slim + requirements)
docker compose build

# Default: chat_stream ON, chat OFF (interactive prompt)
docker compose run --rm app

# Pass CLI flags after the service name
docker compose run --rm app python main.py --chat
docker compose run --rm app python main.py --chat --no-chat-stream
docker compose run --rm app python main.py --chat-stream
```

`docker-compose.yaml` mounts env vars from `.env`, and enables `stdin_open` + `tty` so `input()` and streamed output work in the terminal.

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--chat` | off | Run `chat()` on all providers in parallel |
| `--chat-stream` / `--no-chat-stream` | on | Run `chat_stream()` sequentially (one provider at a time) |

## Notes

- Gemini thinking models (e.g. `gemini-3.8-flash`) count thinking tokens toward `max_output_tokens`. This demo raises Gemini’s limit to `1024` so short answers are less likely to be truncated.
- Anthropic’s Python SDK 1.x no longer accepts `temperature=` on `messages.create`; when set, this project passes it via `extra_body` and retries without it if the model rejects sampling params.
