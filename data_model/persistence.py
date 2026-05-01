from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import get_settings
from data_model.schema import ClauseModel, ContractModel, PipelineRunModel, UserModel


def _connect() -> sqlite3.Connection:
    db_path = Path(get_settings().db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS contracts (
                contract_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                governing_law TEXT,
                effective_date TEXT,
                metadata_json TEXT NOT NULL,
                contract_json TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS clauses (
                clause_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                clause_json TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contracts(contract_id)
            );

            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                provider_used TEXT NOT NULL,
                run_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contracts(contract_id)
            );

            CREATE TABLE IF NOT EXISTS modifications (
                proposal_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                clause_id TEXT NOT NULL,
                proposal_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        # Backward-compatible migration for older local DBs.
        try:
            conn.execute("ALTER TABLE contracts ADD COLUMN contract_json TEXT")
        except sqlite3.OperationalError:
            pass


def create_user(username: str, password: str) -> UserModel:
    from auth.hashing import hash_password

    existing = get_user_by_username(username)
    if existing:
        new_hash = hash_password(password)
        with _connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, is_active = 1 WHERE username = ?",
                (new_hash, username),
            )
        existing.password_hash = new_hash
        existing.is_active = True
        return existing

    user = UserModel(username=username, password_hash=hash_password(password))
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, password_hash, created_at, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.user_id,
                user.username,
                user.password_hash,
                user.created_at.isoformat(),
                int(user.is_active),
            ),
        )
    return user


def get_user_by_username(username: str) -> UserModel | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT user_id, username, password_hash, created_at, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        return None
    return UserModel(
        user_id=row["user_id"],
        username=row["username"],
        password_hash=row["password_hash"],
        created_at=datetime.fromisoformat(row["created_at"]),
        is_active=bool(row["is_active"]),
    )


def authenticate_user(username: str, password: str) -> UserModel | None:
    from auth.hashing import verify_password

    user = get_user_by_username(username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def save_contract(contract: ContractModel) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO contracts (
                contract_id, file_name, document_type, raw_text,
                governing_law, effective_date, metadata_json, contract_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract.contract_id,
                contract.file_name,
                contract.document_type.value,
                contract.raw_text,
                contract.governing_law,
                contract.effective_date,
                json.dumps(contract.metadata),
                contract.model_dump_json(),
                contract.created_at.isoformat(),
            ),
        )
        conn.execute("DELETE FROM clauses WHERE contract_id = ?", (contract.contract_id,))
        for clause in contract.clauses:
            conn.execute(
                """
                INSERT INTO clauses (clause_id, contract_id, clause_json)
                VALUES (?, ?, ?)
                """,
                (clause.clause_id, contract.contract_id, clause.model_dump_json()),
            )


def load_contract(contract_id: str) -> ContractModel | None:
    with _connect() as conn:
        contract_row = conn.execute(
            """
            SELECT contract_id, file_name, document_type, raw_text, governing_law,
                   effective_date, metadata_json, contract_json, created_at
            FROM contracts WHERE contract_id = ?
            """,
            (contract_id,),
        ).fetchone()
        clause_rows = conn.execute(
            "SELECT clause_json FROM clauses WHERE contract_id = ?",
            (contract_id,),
        ).fetchall()

    if not contract_row:
        return None

    contract_json = contract_row["contract_json"]
    if contract_json:
        return ContractModel.model_validate_json(contract_json)

    contract = ContractModel(
        contract_id=contract_row["contract_id"],
        file_name=contract_row["file_name"],
        document_type=contract_row["document_type"],
        raw_text=contract_row["raw_text"],
        governing_law=contract_row["governing_law"],
        effective_date=contract_row["effective_date"],
        metadata=json.loads(contract_row["metadata_json"]),
        created_at=datetime.fromisoformat(contract_row["created_at"]),
        clauses=[],
    )
    contract.clauses = [ClauseModel.model_validate_json(row["clause_json"]) for row in clause_rows]
    return contract


def save_contract_run(run: PipelineRunModel) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (run_id, contract_id, provider_used, run_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.contract_id,
                run.provider_used,
                run.model_dump_json(),
                datetime.now(UTC).isoformat(),
            ),
        )


def load_contract_run(contract_id: str) -> PipelineRunModel | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT run_json FROM runs
            WHERE contract_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (contract_id,),
        ).fetchone()
    if not row:
        return None
    return PipelineRunModel.model_validate_json(row["run_json"])


def save_modification(contract_id: str, clause_id: str, proposal: dict[str, Any]) -> None:
    proposal_id = proposal.get("proposal_id")
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO modifications (proposal_id, contract_id, clause_id, proposal_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                contract_id,
                clause_id,
                json.dumps(proposal),
                datetime.now(UTC).isoformat(),
            ),
        )


def add_audit_event(event_type: str, payload: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload), datetime.now(UTC).isoformat()),
        )
