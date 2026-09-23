"""Allowlisted production migrations for the local Admission ledger.

Migration bytes are security-relevant package data.  The store accepts only
the ordered resources and immutable digests declared here; it never searches
the project tree, network, or an alternate directory.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SqliteAdmissionMigration:
    """One ordered, packaged SQLite Admission-store migration."""

    migration_id: int
    resource_name: str
    sha256: str


MIGRATIONS = (
    SqliteAdmissionMigration(
        migration_id=1,
        resource_name="0001_initial.sql",
        sha256="6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed",
    ),
)

SCHEMA_VERSION = MIGRATIONS[-1].migration_id

__all__ = (
    "MIGRATIONS",
    "SCHEMA_VERSION",
    "SqliteAdmissionMigration",
)
