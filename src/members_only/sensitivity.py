"""Deterministic first-pass sensitivity inspection for proposals."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any, Iterator

from .models import Proposal, SensitivityFinding, SensitivityLevel


_CREDENTIAL_FIELDS = {
    "api_key",
    "apikey",
    "access_token",
    "password",
    "passcode",
    "refresh_token",
    "secret",
    "token",
}

_PERSONAL_FIELDS = {
    "address",
    "date_of_birth",
    "dob",
    "email",
    "phone",
    "phone_number",
    "social_security_number",
    "ssn",
}

_SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:api[_ -]?key|access[_ -]?token)\s*[:=]\s*\S+", re.IGNORECASE),
)


def _field_name(field: str) -> str:
    return field.strip().lower().replace("-", "_").replace(" ", "_")


def _walk_fields(value: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            field = str(key)
            nested_path = f"{path}.{field}" if path else field
            yield from _walk_fields(nested_value, nested_path)
        return

    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            yield from _walk_fields(nested_value, f"{path}[{index}]")
        return

    yield path, value


def inspect_proposal(proposal: Proposal) -> tuple[SensitivityFinding, ...]:
    """Return protection findings for the proposal payload."""

    findings: list[SensitivityFinding] = []
    for field_path, _value in _walk_fields(proposal.payload):
        field = field_path.rsplit(".", 1)[-1]
        if (
            proposal.action == "send_message"
            and _field_name(field) in {"body", "message", "text"}
            and isinstance(_value, str)
        ):
            findings.append(
                SensitivityFinding(
                    category="private_message",
                    level=SensitivityLevel.HIGH,
                    reason="The proposal contains outbound message content.",
                    confidence=1.0,
                    field=field_path,
                )
            )
        if _field_name(field) in _CREDENTIAL_FIELDS:
            findings.append(
                SensitivityFinding(
                    category="credential",
                    level=SensitivityLevel.CRITICAL,
                    reason="The payload contains a credential field.",
                    confidence=1.0,
                    field=field_path,
                )
            )
        elif _field_name(field) in _PERSONAL_FIELDS:
            findings.append(
                SensitivityFinding(
                    category="personal_data",
                    level=SensitivityLevel.HIGH,
                    reason="The payload contains personal information.",
                    confidence=1.0,
                    field=field_path,
                )
            )
        elif isinstance(_value, str) and any(
            pattern.search(_value) for pattern in _SECRET_VALUE_PATTERNS
        ):
            findings.append(
                SensitivityFinding(
                    category="credential",
                    level=SensitivityLevel.CRITICAL,
                    reason="The payload contains a secret-like value.",
                    confidence=0.95,
                    field=field_path,
                )
            )
    return tuple(findings)
