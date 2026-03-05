"""
Database module for SarvaSahay Platform
Provides database connection, session management, and base models
"""

from shared.database.base import Base, get_db, engine, SessionLocal
from shared.database.models import (
    UserProfileDB,
    GovernmentSchemeDB,
    ApplicationDB,
    ApplicationTrackingDB,
    DocumentDB,
    AuditLogDB,
)

__all__ = [
    "Base",
    "get_db",
    "engine",
    "SessionLocal",
    "UserProfileDB",
    "GovernmentSchemeDB",
    "ApplicationDB",
    "ApplicationTrackingDB",
    "DocumentDB",
    "AuditLogDB",
]
