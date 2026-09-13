"""Local SQLite persistence for approvals, capabilities, and receipts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from .models import Approval, Capability, Decision, ExecutionStatus, Receipt


def _datetime_text(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class LocalStore:
    """Persist security records without storing proposal payloads."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._connection = sqlite3.connect(str(path))
        self._connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                member_id TEXT NOT NULL,
                proposal_digest TEXT NOT NULL,
                approved_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                member_id TEXT NOT NULL,
                action TEXT NOT NULL,
                proposal_digest TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS redeemed_capabilities (
                capability_id TEXT PRIMARY KEY,
                redeemed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receipts (
                receipt_id TEXT PRIMARY KEY,
                proposal_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def save_approval(self, approval: Approval) -> None:
        self._connection.execute(
            """
            INSERT INTO approvals
                (approval_id, proposal_id, member_id, proposal_digest, approved_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                approval.approval_id,
                approval.proposal_id,
                approval.member_id,
                approval.proposal_digest,
                _datetime_text(approval.approved_at),
            ),
        )
        self._connection.commit()

    def get_approval(self, approval_id: str) -> Approval | None:
        row = self._connection.execute(
            "SELECT * FROM approvals WHERE approval_id = ?",
            (approval_id,),
        ).fetchone()
        if row is None:
            return None
        return Approval(
            approval_id=row["approval_id"],
            proposal_id=row["proposal_id"],
            member_id=row["member_id"],
            proposal_digest=row["proposal_digest"],
            approved_at=_parse_datetime(row["approved_at"]),
        )

    def save_capability(self, capability: Capability) -> None:
        self._connection.execute(
            """
            INSERT INTO capabilities
                (capability_id, proposal_id, member_id, action,
                 proposal_digest, issued_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                capability.capability_id,
                capability.proposal_id,
                capability.member_id,
                capability.action,
                capability.proposal_digest,
                _datetime_text(capability.issued_at),
                _datetime_text(capability.expires_at),
            ),
        )
        self._connection.commit()

    def get_capability(self, capability_id: str) -> Capability | None:
        row = self._connection.execute(
            "SELECT * FROM capabilities WHERE capability_id = ?",
            (capability_id,),
        ).fetchone()
        if row is None:
            return None
        return Capability(
            capability_id=row["capability_id"],
            proposal_id=row["proposal_id"],
            member_id=row["member_id"],
            action=row["action"],
            proposal_digest=row["proposal_digest"],
            issued_at=_parse_datetime(row["issued_at"]),
            expires_at=_parse_datetime(row["expires_at"]),
        )

    def mark_capability_redeemed(self, capability_id: str, redeemed_at: datetime) -> bool:
        """Atomically mark an existing capability as redeemed once."""

        cursor = self._connection.execute(
            """
            INSERT OR IGNORE INTO redeemed_capabilities (capability_id, redeemed_at)
            SELECT ?, ?
            WHERE EXISTS (
                SELECT 1 FROM capabilities WHERE capability_id = ?
            )
            """,
            (capability_id, _datetime_text(redeemed_at), capability_id),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def save_receipt(self, receipt: Receipt) -> None:
        self._connection.execute(
            """
            INSERT INTO receipts
                (receipt_id, proposal_id, decision, status, summary, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                receipt.receipt_id,
                receipt.proposal_id,
                receipt.decision.value,
                receipt.status.value,
                receipt.summary,
                _datetime_text(receipt.recorded_at),
            ),
        )
        self._connection.commit()

    def get_receipt(self, receipt_id: str) -> Receipt | None:
        row = self._connection.execute(
            "SELECT * FROM receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
        if row is None:
            return None
        return Receipt(
            receipt_id=row["receipt_id"],
            proposal_id=row["proposal_id"],
            decision=Decision(row["decision"]),
            status=ExecutionStatus(row["status"]),
            summary=row["summary"],
            recorded_at=_parse_datetime(row["recorded_at"]),
        )

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "LocalStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
