# AGENTS.md

Chest X-ray screening system. Three services, each with a dedicated agent instruction file in `agents/`. Read the relevant file before working in that service's area.

## Architecture

| Service | Port | Tech | Talks to |
| --- | --- | --- | --- |
| Model Server | `localhost:8001` | FastAPI / Python | nothing (leaf) |
| Backend | `localhost:8000` | FastAPI / Python | Model Server only |
| Frontend | `localhost:3000` | React | Backend only |

Request flow: **Frontend → Backend → Model Server**. The Frontend must never call the Model Server directly; the Model Server must never call anything upstream.

## OpenCode config

`opencode.json` enables the `stitch` (remote MCP) and `playwright` (local MCP) servers. Agent specs and `instructions` live in `agents/`, not inline here.

## Development practices

- **Separate git worktrees** Always make breaking changes in a new fresh git worktree.
- **Do not write excessive comments**
- Install everything in project's directory, try not installing anything in directories outside.
- **Update Docs** After any major change, update the markdown files in /agents directory
- NEVER RUN git add .
