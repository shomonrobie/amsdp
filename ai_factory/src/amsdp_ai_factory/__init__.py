"""AMSDP AI Factory package.

The AMSDP AI Factory is a development-time, CrewAI-based system that
orchestrates specialist software-development agents and workflows for the
AMSDP healthcare microservices product. It is *not* part of the AMSDP
runtime and never acts as an unrestricted autonomous coding agent.

This package exposes:
- ``config.settings`` — validated Factory settings (env-driven).
- ``context`` — governed-document registry, loader, and task-type selectors.
- ``contracts.common`` — shared typed models and validation primitives.
- ``validation.configuration`` — environment/document validation used by
  the CLI ``doctor``/``validate`` commands.

Higher-level subsystems (agents, crews, workflows, tasks, tools, approvals,
runs) are added in later phases.
"""

from __future__ import annotations

__version__ = "0.1.0"
VERSION = __version__
FACTORY_NAME = "AMSDP AI Factory"