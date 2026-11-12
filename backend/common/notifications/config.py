"""Organization notification configuration (Sequence 3, WP6).

Stored on the existing ``organizations.config`` JSON — no new settings table:

    {
      "notification_config": {
        "whatsapp": {"enabled": true,  "provider": "mock"},
        "sms":      {"enabled": false, "provider": "mock"},
        "reminder_lead_minutes": 10
      }
    }

Safe defaults preserve prior behaviour exactly: a database without this key
behaves as "no notifications", so no message is ever sent by surprise.

Channel status values returned to clients
-----------------------------------------
``disabled``       — the organization turned the channel off (default)
``awaiting_setup`` — enabled, but the platform registers no provider at all
``unavailable``    — a provider is named but this build has no adapter for it
``configured``     — enabled and a usable adapter exists; rows may be sent

Credentials are never stored here. Their presence is reported only as a boolean
derived from the environment.
"""

import os

from .providers import declared_providers, implemented_providers, provider_is_usable

CHANNELS = ("whatsapp", "sms")
DEFAULT_PROVIDER = "mock"
ALLOWED_LEAD_MINUTES = (5, 10)
DEFAULT_LEAD_MINUTES = 10
# Minimum gap between two messages for the same appointment + channel.
COOLDOWN_MINUTES = int(os.environ.get("AMSDP_NOTIFICATION_COOLDOWN_MINUTES", "2") or 2)
# Average minutes per consultation, used to estimate the expected visit time
# while the patient is still in the queue.
AVG_SERVICE_MINUTES = int(os.environ.get("AMSDP_AVG_SERVICE_MINUTES", "10") or 10)

STATUS_DISABLED = "disabled"
STATUS_AWAITING_SETUP = "awaiting_setup"
STATUS_UNAVAILABLE = "unavailable"
STATUS_CONFIGURED = "configured"


def credentials_configured(channel: str) -> bool:
    """Whether the environment holds credentials for *channel*'s provider.

    Only the boolean is ever exposed; the value itself is never read here,
    never stored and never logged.
    """
    return bool(os.environ.get(f"AMSDP_{channel.upper()}_API_KEY"))


def _channel_config(raw: dict, channel: str) -> dict:
    enabled = bool(raw.get("enabled", False))
    provider = (raw.get("provider") or DEFAULT_PROVIDER).strip().lower()
    if not implemented_providers():
        status = STATUS_AWAITING_SETUP
    elif not enabled:
        status = STATUS_DISABLED
    elif provider_is_usable(provider):
        status = STATUS_CONFIGURED
    else:
        status = STATUS_UNAVAILABLE
    return {
        "enabled": enabled,
        "provider": provider,
        "status": status,
        "usable": status == STATUS_CONFIGURED,
        "credentials_configured": credentials_configured(channel)
                                  if provider != "mock" else False,
    }


def get_notification_config(org_config=None) -> dict:
    """Normalized, always-valid view of an organization's notification settings."""
    raw = (org_config or {}).get("notification_config") or {}
    lead = raw.get("reminder_lead_minutes", DEFAULT_LEAD_MINUTES)
    try:
        lead = int(lead)
    except (TypeError, ValueError):
        lead = DEFAULT_LEAD_MINUTES
    if lead not in ALLOWED_LEAD_MINUTES:
        lead = DEFAULT_LEAD_MINUTES
    out = {
        "reminder_lead_minutes": lead,
        "cooldown_minutes": COOLDOWN_MINUTES,
        "allowed_lead_minutes": list(ALLOWED_LEAD_MINUTES),
    }
    for channel in CHANNELS:
        out[channel] = _channel_config(raw.get(channel) or {}, channel)
    return out


def merge_notification_config(org_config=None, updates=None) -> dict:
    """Return a NEW config dict with *updates* applied (never mutates input).

    ``updates`` uses flat keys so the HTTP contract stays simple::

        {"whatsapp_enabled": bool, "sms_enabled": bool,
         "whatsapp_provider": str, "sms_provider": str,
         "reminder_lead_minutes": int}

    Validation is the caller's responsibility; unknown keys are ignored here.
    """
    base = dict(org_config or {})
    current = dict(base.get("notification_config") or {})
    updates = updates or {}

    for channel in CHANNELS:
        ch = dict(current.get(channel) or {})
        enabled_key, provider_key = f"{channel}_enabled", f"{channel}_provider"
        if enabled_key in updates and updates[enabled_key] is not None:
            ch["enabled"] = bool(updates[enabled_key])
        if provider_key in updates and updates[provider_key]:
            ch["provider"] = str(updates[provider_key]).strip().lower()
        ch.setdefault("enabled", False)
        ch.setdefault("provider", DEFAULT_PROVIDER)
        current[channel] = ch

    if updates.get("reminder_lead_minutes") is not None:
        current["reminder_lead_minutes"] = int(updates["reminder_lead_minutes"])
    current.setdefault("reminder_lead_minutes", DEFAULT_LEAD_MINUTES)

    base["notification_config"] = current
    return base


def validate_updates(updates: dict) -> list[str]:
    """Return a list of human-readable validation errors (empty when valid)."""
    errors = []
    lead = updates.get("reminder_lead_minutes")
    if lead is not None and lead not in ALLOWED_LEAD_MINUTES:
        errors.append(
            f"reminder_lead_minutes must be one of {list(ALLOWED_LEAD_MINUTES)}")
    for channel in CHANNELS:
        provider = updates.get(f"{channel}_provider")
        if provider:
            name = str(provider).strip().lower()
            if name not in declared_providers() or name not in implemented_providers():
                errors.append(
                    f"{channel}_provider '{provider}' is not available on this "
                    f"platform (available: {list(implemented_providers())})")
    return errors


def public_view(organization_id: str, org_config=None) -> dict:
    """Client-safe configuration payload (no secrets, no credentials)."""
    from .providers import describe_platform
    cfg = get_notification_config(org_config)
    return {
        "organization_id": organization_id,
        "whatsapp": cfg["whatsapp"],
        "sms": cfg["sms"],
        "reminder_lead_minutes": cfg["reminder_lead_minutes"],
        "allowed_lead_minutes": cfg["allowed_lead_minutes"],
        "cooldown_minutes": cfg["cooldown_minutes"],
        "platform": describe_platform(),
    }
