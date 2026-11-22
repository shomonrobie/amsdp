"""Check the Alembic revision graph without alembic (read-only).

This host has no ``alembic`` installed, so ``alembic heads`` cannot be run.  The
revision graph is nevertheless decidable from the source: every version file
declares ``revision`` and ``down_revision`` as literals.  This checker parses them,
prints the chain, and reports the heads — the fact that decides whether
``alembic upgrade head`` will refuse to run with "multiple heads".

It also answers the counterfactual that the W2 report asks about: if the
``a7c3f19d2b64`` revision (QUE-006/W2) were reparented from ``f8a2b3c4d5e6`` to the
true head ``a9c4e1f7b2d8``, how many heads would remain?

Usage::

    python scripts/que-006-w3-voice-config/check_migration_graph.py
"""
from __future__ import annotations

import ast
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
VERSIONS = os.path.join(ROOT, "backend", "alembic", "versions")


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None


def read_graph():
    """``{revision: (down_revision, filename)}`` for every version file."""
    graph = {}
    for path in sorted(glob.glob(os.path.join(VERSIONS, "*.py"))):
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        values = {}
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id in ("revision", "down_revision"):
                    values[node.target.id] = _literal(node.value)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in (
                            "revision", "down_revision"):
                        values[target.id] = _literal(node.value)
        if values.get("revision"):
            graph[values["revision"]] = (values.get("down_revision"),
                                         os.path.basename(path))
    return graph


def parents_of(down):
    if down is None:
        return []
    if isinstance(down, str):
        return [down]
    return [str(item) for item in down]


def heads(graph):
    claimed = set()
    for down, _name in graph.values():
        claimed.update(parents_of(down))
    return sorted(revision for revision in graph if revision not in claimed)


def chain(graph, revision, seen=None):
    seen = seen or []
    down, _name = graph[revision]
    seen.append(revision)
    for parent in parents_of(down):
        if parent in graph:
            chain(graph, parent, seen)
        else:
            seen.append(parent + " (missing)")
    return seen


def main() -> int:
    graph = read_graph()
    print(f"{len(graph)} revisions in backend/alembic/versions")
    current = heads(graph)
    print("heads: " + ", ".join(current))
    for revision in current:
        print("  " + " <- ".join(chain(graph, revision)))

    broken = [r for r, (down, _n) in graph.items()
              if any(p not in graph for p in parents_of(down))]
    if broken:
        print("missing parents: " + ", ".join(sorted(broken)))

    repaired = dict(graph)
    target = "a7c3f19d2b64"
    if target in repaired and repaired[target][0] == "f8a2b3c4d5e6":
        repaired[target] = ("a9c4e1f7b2d8", repaired[target][1])
        after = heads(repaired)
        print("if " + target + " is reparented to a9c4e1f7b2d8, heads: "
              + ", ".join(after)
              + ("  <-- single head" if len(after) == 1 else ""))

    # A single head is the only state in which `alembic upgrade head` runs.
    return 0 if len(current) == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
