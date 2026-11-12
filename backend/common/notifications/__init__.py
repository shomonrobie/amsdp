"""AMSDP notification subsystem (Sequence 3 / M9-D outbox).

Modules
-------
``config``    — org-level channel configuration (default: all channels off)
``providers`` — provider-neutral delivery boundary + mock adapter
``outbox``    — persistent row operations (enqueue, cancel, deliver, retry)
``hooks``     — best-effort, exception-swallowing lifecycle hooks
``worker``    — standalone polling worker (``python3 -m common.notifications.worker``)

Design rules honoured here:
- A notification failure never fails or rolls back a business operation.
- Nothing is delivered unless the organization enabled the channel AND the
  platform exposes a working provider adapter.
- Secrets live in the environment only; nothing here logs bodies or credentials.
"""

from .config import get_notification_config  # noqa: F401
