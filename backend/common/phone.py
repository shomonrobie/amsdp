"""Bangladeshi mobile-number normalisation — the single authority.

Why this exists (AMSDP-FACILITY-DOCTOR-01)
------------------------------------------
The same doctor was entered as ``01711111111``, ``+8801711111111``,
``880 1711-111111`` and ``1711111111`` on different days, so search by phone
found nothing and duplicate detection could not work.  Rather than scatter
``replace("+88", "")`` calls through the services, every service calls
:func:`normalize_bd_mobile` and stores the canonical national form
(``01XXXXXXXXX``).

Scope: **Bangladeshi mobile numbers only** (BR: the MVP is single-country, and
``Asia/Dhaka`` is the default organization timezone).  A number that is not a
valid BD mobile is rejected by the caller — the services turn the ``ValueError``
into a 422, they never store a guess.

Format accepted (all of these normalise to ``01711111111``):

===========================  ==========================================
``01711111111``              canonical national form
``+8801711111111``           international, with ``+``
``8801711111111``            international, without ``+``
``1711111111``               national without the trunk ``0``
``017 1111 1111``            spaces
``017-1111-1111``            dashes
``(017) 11111111``           parentheses
===========================  ==========================================

The operator prefix must be ``013``–``019`` (the allocated BD mobile ranges);
``012``/``010`` (PSTN) and anything shorter/longer is rejected.
"""

import re

#: Canonical national form: 11 digits, operator prefix 013–019.
_BD_MOBILE = re.compile(r"^01[3-9]\d{8}$")

#: Characters that carry no information in a written phone number.
_SEPARATORS = re.compile(r"[\s\-().]")

#: Digits only — used after the separators are gone.
_NON_DIGITS = re.compile(r"\D")


class InvalidMobileNumber(ValueError):
    """Raised when a value cannot be a Bangladeshi mobile number."""


def normalize_bd_mobile(value) -> str:
    """Return *value* in canonical national form (``01XXXXXXXXX``).

    Raises :class:`InvalidMobileNumber` (a ``ValueError``) when the value is
    empty or is not a valid Bangladeshi mobile number.  Never returns a
    partially-cleaned value: callers must either get a valid number or an
    exception.
    """
    if value is None:
        raise InvalidMobileNumber("mobile number is required")
    raw = str(value).strip()
    if not raw:
        raise InvalidMobileNumber("mobile number is required")

    cleaned = _SEPARATORS.sub("", raw)
    if cleaned.startswith("+"):
        # A leading "+" is meaningful (international); keep the digits only.
        cleaned = _NON_DIGITS.sub("", cleaned)
        international = True
    else:
        cleaned = _NON_DIGITS.sub("", cleaned)
        international = False

    if cleaned.startswith("880"):
        # 8801711111111 -> 01711111111
        national = "0" + cleaned[3:]
    elif cleaned.startswith("01"):
        national = cleaned
    elif international:
        raise InvalidMobileNumber(
            "invalid Bangladeshi mobile number: country code must be +880")
    elif len(cleaned) == 10 and cleaned.startswith("1"):
        # 1711111111 -> 01711111111 (trunk zero omitted)
        national = "0" + cleaned
    else:
        raise InvalidMobileNumber("invalid Bangladeshi mobile number")

    if not _BD_MOBILE.match(national):
        raise InvalidMobileNumber(
            "invalid Bangladeshi mobile number (expected 01[3-9]XXXXXXXX)")
    return national


def is_valid_bd_mobile(value) -> bool:
    """True when *value* normalises to a Bangladeshi mobile number."""
    try:
        normalize_bd_mobile(value)
        return True
    except InvalidMobileNumber:
        return False


def format_bd_mobile(value, style: str = "national") -> str:
    """Display helper for an already-valid number.

    ``style="national"`` (default) → ``01711111111``;
    ``style="e164"``             → ``+8801711111111``;
    ``style="spaced"``           → ``017 1111 1111`` (printed artefacts only).

    An unusable value is returned unchanged rather than raising: this is a
    presentation helper, and a malformed legacy row must still render.
    """
    try:
        national = normalize_bd_mobile(value)
    except InvalidMobileNumber:
        return "" if value is None else str(value)
    if style == "e164":
        return "+88" + national
    if style == "spaced":
        return f"{national[:3]} {national[3:7]} {national[7:]}"
    return national
