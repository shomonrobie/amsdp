"""Standalone notification worker (Sequence 3, WP4).

Run it next to the API services — it is deliberately **not** started inside any
FastAPI process, so an API restart can never duplicate sends:

    cd backend
    python3 -m common.notifications.worker --once            # drain due rows
    python3 -m common.notifications.worker --interval 30      # poll loop

Deployment (a compose service, systemd unit or cron entry) is a separate,
explicit act and is **not** part of Sequence 3 — this module only makes the
worker runnable and testable.
"""

import argparse
import logging
import time as time_module

from ..database import SessionFactory
from . import outbox

logger = logging.getLogger(__name__)


def run_once(limit: int = 50) -> dict:
    """Deliver everything due right now and commit. Safe to call from tests."""
    session = SessionFactory()
    try:
        summary = outbox.process_due(session, limit=limit)
        session.commit()
        return summary
    except Exception:
        session.rollback()
        logger.warning("notification worker run failed", exc_info=False)
        raise
    finally:
        session.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AMSDP notification worker")
    parser.add_argument("--interval", type=int, default=30,
                        help="seconds between polls (default 30)")
    parser.add_argument("--limit", type=int, default=50,
                        help="maximum rows per poll (default 50)")
    parser.add_argument("--once", action="store_true",
                        help="process a single batch and exit")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if args.once:
        summary = run_once(limit=args.limit)
        logger.info("notification worker batch: processed=%s sent=%s failed=%s",
                    summary["processed"], summary["sent"], summary["failed"])
        return 0

    logger.info("notification worker started (interval=%ss)", args.interval)
    try:
        while True:
            try:
                run_once(limit=args.limit)
            except Exception:  # keep the loop alive; the next poll may succeed
                logger.warning("notification worker poll failed; retrying")
            time_module.sleep(max(args.interval, 1))
    except KeyboardInterrupt:
        logger.info("notification worker stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
