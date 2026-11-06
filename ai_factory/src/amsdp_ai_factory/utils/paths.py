"""Repository-root discovery.

The AI Factory must locate the AMSDP repository root reliably before
loading documents or writing artifacts. Resolution order:

1. ``AMSDP_FACTORY_REPO_ROOT`` environment variable (validated as an
   existing directory) or the explicitly configured setting;
2. walking upwards from the start directory (default: the current working
   directory) to the first ancestor containing a ``.git`` marker;
3. if no marker is found, the start directory itself is returned so callers
   can report it (validation flags the missing marker as a warning).
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_REPO_ROOT = "AMSDP_FACTORY_REPO_ROOT"
_REPO_ROOT_MARKERS: tuple[str, ...] = (".git",)


def discover_repo_root(start: Path | None = None) -> Path:
    """Return the repository root, preferring an explicit env override."""
    explicit = os.environ.get(ENV_REPO_ROOT)
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not candidate.is_dir():
            raise ValueError(
                f"{ENV_REPO_ROOT} points to a non-directory: {explicit!r}"
            )
        return candidate

    start_dir = (start or Path.cwd()).resolve()
    for probe in (start_dir, *start_dir.parents):
        if any((probe / marker).exists() for marker in _REPO_ROOT_MARKERS):
            return probe
    # No marker found: return the best effort so validation can report it.
    return start_dir


def is_within(root: Path, candidate: Path) -> bool:
    """True if ``candidate`` resolves inside ``root`` (path containment)."""
    root_resolved = root.resolve()
    candidate_resolved = candidate.expanduser().resolve()
    return candidate_resolved == root_resolved or root_resolved in candidate_resolved.parents