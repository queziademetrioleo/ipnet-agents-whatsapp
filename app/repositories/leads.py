from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import psycopg
from psycopg import sql


@dataclass(slots=True)
class LeadRecord:
    lead_id: str
    name: str
    email: str
    phone: str
    subject: str
    notes: str
    created_at: datetime


class LeadRepository:
    def __init__(self, dsn: str, schema: str) -> None:
        self.dsn = dsn
        self.schema = schema

    def ensure_schema(self) -> None:
        schema_sql = sql.Identifier(self.schema)
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(schema_sql))
                cur.execute(
                    sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {}.leads (
                            lead_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            email TEXT NOT NULL,
                            phone TEXT NOT NULL DEFAULT '',
                            subject TEXT NOT NULL,
                            notes TEXT NOT NULL DEFAULT '',
                            created_at TIMESTAMPTZ NOT NULL
                        )
                        """
                    ).format(schema_sql)
                )
            conn.commit()

    def create(
        self,
        name: str,
        email: str,
        phone: str,
        subject: str,
        notes: str,
    ) -> LeadRecord:
        now = datetime.now(timezone.utc)
        lead_id = str(uuid4())
        schema_sql = sql.Identifier(self.schema)

        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        """
                        INSERT INTO {}.leads (
                            lead_id,
                            name,
                            email,
                            phone,
                            subject,
                            notes,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                    ).format(schema_sql),
                    (lead_id, name, email, phone, subject, notes, now),
                )
            conn.commit()

        return LeadRecord(
            lead_id=lead_id,
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            notes=notes,
            created_at=now,
        )

