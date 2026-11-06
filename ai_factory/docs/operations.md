# AI Factory Operations

## Setup

```bash
# Supported environment: repository .venv313 (Python 3.13)
cd /home/shomonrobie/amsdp/ai_factory
PYTHONPATH=src /home/shomonrobie/amsdp/.venv313/bin/python -m unittest discover -s tests -p 'test_*.py'
```

No provider configuration is needed for stub mode.

## CLI

```bash
cd /home/shomonrobie/amsdp/ai_factory
AILI=/home/shomonrobie/amsdp/.venv313/bin/python
PYTHONPATH=src $AILI -c "from amsdp_ai_factory.cli import main; main()" --help
```

Core commands: `version`, `doctor`, `docs-status`, `agents`, `workflows`,
`task-new`, `task-list`, `task-show`, `run-workflow`, `approve`, `resume`,
`run-status`.

## Safe stub run (no model credentials)

```bash
PYTHONPATH=src $AILI -c "from amsdp_ai_factory.cli import main; main()" task-new \
  --title "Queue reorder design" --workflow-id WF-01
# -> created task AMSDP-000001 ...
PYTHONPATH=src $AILI -c "from amsdp_ai_factory.cli import main; main()" \
  run-workflow AMSDP-000001 WF-01 --mode stub
# -> pauses: awaiting_approval
PYTHONPATH=src $AILI -c "from amsdp_ai_factory.cli import main; main()" \
  approve AMSDP-000001 approved --actor project_owner
PYTHONPATH=src $AILI -c "from amsdp_ai_factory.cli import main; main()" \
  resume AMSDP-000001 --mode stub
# -> succeeded
```

Stub artifacts are explicitly labeled `[STUB-SYNTHETIC]` and are never
treated as verified product work.

## Live execution (explicitly gated)

Only after all three of these are true, run with `--mode live`:

1. `AMSDP_FACTORY_MODEL_PROVIDER` set
2. `AMSDP_FACTORY_MODEL_ID` set
3. `AMSDP_FACTORY_LIVE_EXECUTION_ALLOWED=1` exported explicitly

The live path is implemented but was not exercised in Phase 4 (no provider
was authorized); its gate logic is unit-tested.

## Run records and retention

- Tasks: `ai_factory/var/tasks/<task_id>.json`
- Runs: `ai_factory/runs/RUN-*.json`
- Workspaces: `ai_factory/var/workspaces/<task_id>/`

All three directories are git-ignored. Records never contain secrets (the
run recorder redacts on write) or real patient data. Cleanup of old records
is a separate, human-approved operation; the factory never deletes records
itself.

## Failure diagnostics

- Check the task record (`task-show`) for `history`, `failure_info`, and
  `escalation_notes`.
- Check the run record (`run-status` then `runs/RUN-*.json`) for stage
  statuses, checks, and errors.
- A failed run stops downstream stages; retries are bounded.
## Retry limits and cost controls

- `default_max_retries` in FactorySettings (default 2).
- Each stage tracks retry_count in the run record.
- No per-run budget cap exists yet; monitor via `run-status` and the run
  record's stage error/retry fields.

## Disposable database note

The `disposable_db` tool uses **SQLite in-memory** for structure validation.
Production schema testing (PostgreSQL-specific features) requires a separate,
human-approved process with a real database instance.