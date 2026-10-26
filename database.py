
# database.py

import sqlite3
from datetime import datetime

DB_NAME = "ai_sentinel.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the requests table if it does not exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                summary TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending'
                    CHECK (
                        status IN (
                            'Pending',
                            'In Progress',
                            'Resolved'
                        )
                    ),
                created_at TEXT NOT NULL
            )
        """)


def save_request(description, analysis):
    """Save a human-approved analysis."""
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO requests (
                description,
                category,
                priority,
                summary,
                action,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            description,
            analysis["category"],
            analysis["priority"],
            analysis["summary"],
            analysis["action"],
            "Pending",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))


def get_all_requests():
    """Return all requests, newest first."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, description, category, priority,
                   summary, action, status, created_at
            FROM requests
            ORDER BY id DESC
        """).fetchall()

    return [dict(row) for row in rows]


def update_request_status(request_id, status):
    """Update a request's workflow status."""
    allowed_statuses = {
        "Pending",
        "In Progress",
        "Resolved",
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid workflow status")

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE requests
            SET status = ?
            WHERE id = ?
        """, (status, request_id))

        if cursor.rowcount == 0:
            raise ValueError("Request not found")


def get_dashboard_stats():
    """Calculate metrics from stored requests."""
    with get_connection() as connection:
        row = connection.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(
                    SUM(CASE
                        WHEN priority = 'High' THEN 1 ELSE 0
                    END), 0
                ) AS high,
                COALESCE(
                    SUM(CASE
                        WHEN status = 'Pending' THEN 1 ELSE 0
                    END), 0
                ) AS pending,
                COALESCE(
                    SUM(CASE
                        WHEN status = 'Resolved' THEN 1 ELSE 0
                    END), 0
                ) AS resolved
            FROM requests
        """).fetchone()

    return dict(row)
