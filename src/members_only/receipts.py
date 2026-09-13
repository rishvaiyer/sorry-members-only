"""Safe trace events and receipt creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from types import MappingProxyType
from typing import Any, Mapping

from .models import Decision, ExecutionStatus, Proposal, Receipt


_UNSAFE_DETAIL_KEYS = {
    "api_key",
    "body",
    "content",
    "message",
    "password",
    "payload",
    "secret",
    "token",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """A safe event containing metadata, never the original proposal payload."""

    event: str
    proposal_id: str
    details: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.event.strip():
            raise ValueError("event must be a non-empty string")
        if not self.proposal_id.strip():
            raise ValueError("proposal_id must be a non-empty string")
        unsafe_keys = {
            str(key).strip().lower().replace("-", "_") for key in self.details
        } & _UNSAFE_DETAIL_KEYS
        if unsafe_keys:
            raise ValueError("trace details cannot contain payload-like fields")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "proposal_id": self.proposal_id,
            "occurred_at": self.occurred_at.isoformat(),
            "details": _json_value(self.details),
        }


class TraceRecorder:
    """Collect structured trace events for tests, demos, or later log sinks."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        event: str,
        proposal_id: str,
        details: Mapping[str, Any] | None = None,
    ) -> TraceEvent:
        trace_event = TraceEvent(event, proposal_id, details or {})
        self._events.append(trace_event)
        return trace_event

    def to_jsonl(self) -> str:
        return "\n".join(
            json.dumps(event.to_dict(), sort_keys=True) for event in self._events
        )


def create_receipt(
    proposal: Proposal,
    *,
    decision: Decision,
    status: ExecutionStatus,
    summary: str,
) -> Receipt:
    """Create a receipt without accepting or storing a proposal payload."""

    return Receipt(
        proposal_id=proposal.proposal_id,
        decision=decision,
        status=status,
        summary=summary,
    )
