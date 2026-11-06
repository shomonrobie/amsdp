# AMSDP AI Factory

CrewAI-based development-time system that plans, implements, reviews, and
documents AMSDP under a controlled, auditable, human-gated workflow model.

This repository directory contains ONLY the AI Factory. AMSDP runtime
services live under `backend/` / `frontend/` and are out of scope here.

> **Status:** All phases complete. AILI provides **10 executable workflows**,
> 11 specialist agents, 13 active tools, approval service, mock/live execution,
> CLI, and 232 passing tests — ready for the MediCore graduation project.
> See [`docs/workflows.md`](docs/workflows.md) for workflow statuses and
> [`docs/architecture.md`](docs/architecture.md) for recorded decisions.

## Quick start (development)

```bash
cd ai_factory
PYTHONPATH=src .venv313/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

(The repository-level Python 3.13 environment is `.venv313`; see
`docs/architecture.md` for why.)

No model provider is required to run the test suite: all automated tests use
stub execution and local synthetic fixtures.