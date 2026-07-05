from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel
from returns.result import Failure, Success

from recallops.errors import AppError, AppResult, ErrorKind
from recallops.models import (
    ConflictRecord,
    MemoryRecord,
    MemoryStatus,
    OperationEvent,
)

M = TypeVar("M", bound=BaseModel)


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def initialize(self) -> AppResult[None]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        project TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        status TEXT NOT NULL,
                        payload TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_memories_project_status
                        ON memories(project, status);
                    CREATE TABLE IF NOT EXISTS conflicts (
                        id TEXT PRIMARY KEY,
                        project TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        resolved INTEGER NOT NULL,
                        payload TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        project TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload TEXT NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_events_project_created
                        ON events(project, created_at DESC);
                    CREATE TABLE IF NOT EXISTS metrics (
                        project TEXT NOT NULL,
                        name TEXT NOT NULL,
                        value INTEGER NOT NULL,
                        PRIMARY KEY(project, name)
                    );
                    CREATE TABLE IF NOT EXISTS idempotency (
                        key TEXT PRIMARY KEY,
                        operation TEXT NOT NULL,
                        resource_id TEXT NOT NULL
                    );
                    """
                )
            return Success(None)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not initialize RecallOps storage.", exc))

    def reset_project(self, project: str) -> AppResult[None]:
        try:
            with self._connect() as connection:
                for table in ("memories", "conflicts", "events", "metrics"):
                    connection.execute(f"DELETE FROM {table} WHERE project = ?", (project,))
                connection.execute(
                    "DELETE FROM idempotency WHERE resource_id LIKE ?",
                    (f"{project}:%",),
                )
            return Success(None)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not reset the demo project.", exc))

    def save_memory(self, memory: MemoryRecord) -> AppResult[MemoryRecord]:
        return self._upsert_model(
            """
            INSERT INTO memories(id, project, subject, status, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                subject = excluded.subject,
                status = excluded.status,
                payload = excluded.payload
            """,
            (
                str(memory.id),
                memory.project,
                memory.subject,
                memory.status.value,
                memory.model_dump_json(),
            ),
            memory,
        )

    def get_memory(self, memory_id: UUID) -> AppResult[MemoryRecord]:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT payload FROM memories WHERE id = ?", (str(memory_id),)
                ).fetchone()
            if row is None:
                return Failure(
                    AppError(
                        ErrorKind.NOT_FOUND,
                        "Memory was not found.",
                        {"memory_id": str(memory_id)},
                    )
                )
            return Success(MemoryRecord.model_validate_json(str(row["payload"])))
        except (sqlite3.Error, ValueError) as exc:
            return Failure(self._error("Could not load memory.", exc))

    def list_memories(
        self,
        project: str,
        statuses: Iterable[MemoryStatus] | None = None,
    ) -> AppResult[tuple[MemoryRecord, ...]]:
        try:
            query = "SELECT payload FROM memories WHERE project = ?"
            params: list[Any] = [project]
            status_list = list(statuses or ())
            if status_list:
                placeholders = ", ".join("?" for _ in status_list)
                query += f" AND status IN ({placeholders})"
                params.extend(status.value for status in status_list)
            query += " ORDER BY rowid DESC"
            with self._connect() as connection:
                rows = connection.execute(query, params).fetchall()
            return Success(
                tuple(MemoryRecord.model_validate_json(str(row["payload"])) for row in rows)
            )
        except (sqlite3.Error, ValueError) as exc:
            return Failure(self._error("Could not list memories.", exc))

    def active_for_subject(self, project: str, subject: str) -> AppResult[MemoryRecord | None]:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT payload FROM memories
                    WHERE project = ? AND subject = ? AND status = ?
                    ORDER BY rowid DESC LIMIT 1
                    """,
                    (project, subject, MemoryStatus.ACTIVE.value),
                ).fetchone()
            if row is None:
                return Success(None)
            return Success(MemoryRecord.model_validate_json(str(row["payload"])))
        except (sqlite3.Error, ValueError) as exc:
            return Failure(self._error("Could not find current project truth.", exc))

    def save_conflict(self, conflict: ConflictRecord) -> AppResult[ConflictRecord]:
        return self._upsert_model(
            """
            INSERT INTO conflicts(id, project, subject, resolved, payload)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                resolved = excluded.resolved,
                payload = excluded.payload
            """,
            (
                str(conflict.id),
                conflict.project,
                conflict.subject,
                int(conflict.resolved),
                conflict.model_dump_json(),
            ),
            conflict,
        )

    def list_conflicts(
        self, project: str, unresolved_only: bool = False
    ) -> AppResult[tuple[ConflictRecord, ...]]:
        try:
            query = "SELECT payload FROM conflicts WHERE project = ?"
            params: list[Any] = [project]
            if unresolved_only:
                query += " AND resolved = 0"
            query += " ORDER BY rowid DESC"
            with self._connect() as connection:
                rows = connection.execute(query, params).fetchall()
            return Success(
                tuple(ConflictRecord.model_validate_json(str(row["payload"])) for row in rows)
            )
        except (sqlite3.Error, ValueError) as exc:
            return Failure(self._error("Could not list conflicts.", exc))

    def add_event(self, event: OperationEvent) -> AppResult[OperationEvent]:
        return self._upsert_model(
            "INSERT OR REPLACE INTO events(id, project, created_at, payload) VALUES (?, ?, ?, ?)",
            (
                str(event.id),
                event.project,
                event.created_at.isoformat(),
                event.model_dump_json(),
            ),
            event,
        )

    def list_events(self, project: str, limit: int = 50) -> AppResult[tuple[OperationEvent, ...]]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT payload FROM events
                    WHERE project = ?
                    ORDER BY created_at DESC LIMIT ?
                    """,
                    (project, limit),
                ).fetchall()
            return Success(
                tuple(OperationEvent.model_validate_json(str(row["payload"])) for row in rows)
            )
        except (sqlite3.Error, ValueError) as exc:
            return Failure(self._error("Could not list events.", exc))

    def increment_metric(self, project: str, name: str) -> AppResult[int]:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO metrics(project, name, value) VALUES (?, ?, 1)
                    ON CONFLICT(project, name) DO UPDATE SET value = value + 1
                    """,
                    (project, name),
                )
                row = connection.execute(
                    "SELECT value FROM metrics WHERE project = ? AND name = ?",
                    (project, name),
                ).fetchone()
            return Success(int(row["value"]) if row else 0)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not update project metrics.", exc))

    def get_metric(self, project: str, name: str) -> AppResult[int]:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT value FROM metrics WHERE project = ? AND name = ?",
                    (project, name),
                ).fetchone()
            return Success(int(row["value"]) if row else 0)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not load project metrics.", exc))

    def get_idempotent_resource(self, key: str, operation: str) -> AppResult[str | None]:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT resource_id FROM idempotency WHERE key = ? AND operation = ?",
                    (key, operation),
                ).fetchone()
            return Success(str(row["resource_id"]) if row else None)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not check idempotency key.", exc))

    def save_idempotency(self, key: str, operation: str, resource_id: str) -> AppResult[None]:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO idempotency(key, operation, resource_id)
                    VALUES (?, ?, ?)
                    """,
                    (key, operation, resource_id),
                )
            return Success(None)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not save idempotency key.", exc))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _upsert_model(self, query: str, params: tuple[Any, ...], model: M) -> AppResult[M]:
        try:
            with self._connect() as connection:
                connection.execute(query, params)
            return Success(model)
        except sqlite3.Error as exc:
            return Failure(self._error("Could not persist RecallOps state.", exc))

    @staticmethod
    def _error(message: str, cause: Exception) -> AppError:
        return AppError(ErrorKind.PERSISTENCE, message, cause=cause)
