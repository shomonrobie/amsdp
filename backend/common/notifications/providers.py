"""Provider-neutral notification delivery boundary (Sequence 3, WP4).

Why this exists
---------------
Real WhatsApp/SMS delivery is **blocked on product-owner approval** (provider,
account, sender ID, approved template, credentials, cost). This module defines
the *only* seam the rest of the system talks to, so adding a real provider later
is a single adapter class — no outbox, no hook and no API change.

Hard rules
----------
- An adapter NEVER logs recipient numbers or message bodies.
- ``ProviderResult.delivered`` may only be True when the provider itself
  confirmed delivery. The mock adapter therefore never sets it: "accepted by
  provider" (``sent``) and "delivered" are separate states.
- An adapter that is not registered in ``_ADAPTERS`` cannot be selected, even if
  it is named in the platform allow-list or in an organization's config.

Environment
-----------
``AMSDP_NOTIFICATION_PROVIDERS`` — comma-separated platform allow-list of
provider names (default ``"mock"``). Declaring a provider here does not
implement it; only a registered adapter can send.
"""

import os
import uuid
from dataclasses import dataclass


class ProviderUnavailable(Exception):
    """Raised when no usable adapter exists for the configured provider."""


@dataclass(frozen=True)
class ProviderResult:
    """Outcome of a single delivery attempt."""

    ok: bool
    provider: str
    provider_message_id: str = ""
    delivered: bool = False
    error: str = ""
    retryable: bool = True


class NotificationProvider:
    """Base adapter contract."""

    name = "base"
    supports_delivery_receipts = False

    def __init__(self, channel: str = ""):
        self.channel = channel

    def send(self, *, recipient: str, body: str,
             notification_type: str, payload: dict | None = None) -> ProviderResult:
        raise NotImplementedError


class MockNotificationProvider(NotificationProvider):
    """Deterministic, offline adapter used for tests and demos.

    It accepts every well-formed message, assigns a synthetic provider message
    id, and reports ``delivered=False`` because no real handset was involved.
    """

    name = "mock"
    supports_delivery_receipts = False

    def send(self, *, recipient: str, body: str,
             notification_type: str, payload: dict | None = None) -> ProviderResult:
        if not recipient or not body:
            return ProviderResult(ok=False, provider=self.name,
                                  error="missing recipient or body", retryable=False)
        return ProviderResult(ok=True, provider=self.name,
                              provider_message_id=f"mock-{uuid.uuid4().hex[:16]}",
                              delivered=False)


_ADAPTERS = {
    MockNotificationProvider.name: MockNotificationProvider,
}


def declared_providers() -> tuple[str, ...]:
    """Provider names the platform currently allows (env allow-list)."""
    raw = os.environ.get("AMSDP_NOTIFICATION_PROVIDERS", "mock")
    return tuple(p.strip().lower() for p in raw.split(",") if p.strip())


def implemented_providers() -> tuple[str, ...]:
    """Provider names that actually have an adapter in this build."""
    return tuple(sorted(_ADAPTERS))


def provider_is_usable(name: str) -> bool:
    name = (name or "").strip().lower()
    return name in declared_providers() and name in _ADAPTERS


def get_provider(name: str, channel: str = "") -> NotificationProvider:
    """Return an adapter for *name* or raise :class:`ProviderUnavailable`."""
    name = (name or "").strip().lower()
    if name not in _ADAPTERS:
        raise ProviderUnavailable(f"provider '{name}' has no adapter in this build")
    if name not in declared_providers():
        raise ProviderUnavailable(f"provider '{name}' is not enabled on this platform")
    return _ADAPTERS[name](channel=channel)


def describe_platform() -> dict:
    """Non-secret platform capability description (safe to return over HTTP)."""
    declared = declared_providers()
    implemented = implemented_providers()
    real = [p for p in declared if p != "mock"]
    return {
        "declared_providers": list(declared),
        "implemented_providers": list(implemented),
        "real_provider_available": any(p in implemented for p in real),
        "integration_status": "mock-only" if not any(p in implemented for p in real)
                              else "provider-registered",
    }
