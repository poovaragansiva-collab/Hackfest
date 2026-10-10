"""Local SQLite Persistence Layer for Real Generation Records and Analytics.

Persists real successful generation records locally.
Never stores mock data, fake records, or simulated runs.
Provides genuine empty states and authentic aggregate metrics.
"""

import sqlite3
import os
import base64
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "generations.db")

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs")


def get_outputs_dir() -> str:
    """Returns absolute path to controlled outputs directory and ensures it exists."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    return OUTPUTS_DIR


def save_output_artifact(job_id: str, image_url: str, format_hint: str = "png") -> Optional[str]:
    """Saves generated image artifact to the controlled outputs directory.
    
    Returns the relative API endpoint URL (e.g. '/api/v1/outputs/{job_id}.png')
    or None if persistence could not be completed.
    """
    if not job_id or not image_url:
        return None

    try:
        out_dir = get_outputs_dir()
        fmt = format_hint.lower().strip() if format_hint else "png"

        if image_url.startswith("data:image/"):
            header, data_part = image_url.split(",", 1)
            if "png" in header:
                fmt = "png"
            elif "jpeg" in header or "jpg" in header:
                fmt = "jpg"
            elif "webp" in header:
                fmt = "webp"
            elif "svg" in header:
                fmt = "svg"

            filename = f"{job_id}.{fmt}"
            filepath = os.path.join(out_dir, filename)

            if fmt == "svg":
                if ";base64" in header:
                    svg_content = base64.b64decode(data_part).decode("utf-8", errors="replace")
                else:
                    svg_content = urllib.parse.unquote(data_part)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(svg_content)
            else:
                binary_data = base64.b64decode(data_part)
                with open(filepath, "wb") as f:
                    f.write(binary_data)

            return f"/api/v1/outputs/{filename}"

        return None
    except Exception:
        return None


def _get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes the database schema if not present."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                negative_prompt TEXT,
                inferred_purpose TEXT NOT NULL,
                recommended_tier TEXT NOT NULL,
                selected_tier TEXT NOT NULL,
                tier_overridden INTEGER NOT NULL DEFAULT 0,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                steps INTEGER NOT NULL,
                elapsed_seconds REAL NOT NULL,
                compute_work_units REAL NOT NULL,
                savings_percent REAL NOT NULL,
                model TEXT NOT NULL,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                image_url TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON generation_records(timestamp DESC)")
        conn.commit()


def save_generation_record(record: Dict[str, Any]) -> None:
    """Saves a real successful generation execution to the database."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO generation_records (
                job_id, timestamp, prompt, negative_prompt,
                inferred_purpose, recommended_tier, selected_tier,
                tier_overridden, width, height, steps,
                elapsed_seconds, compute_work_units, savings_percent,
                model, provider, status, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("job_id"),
                record.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                record.get("prompt"),
                record.get("negative_prompt", ""),
                record.get("inferred_purpose", "General-purpose educational request"),
                record.get("recommended_tier", "standard"),
                record.get("selected_tier", "standard"),
                1 if record.get("tier_overridden") else 0,
                record.get("width", 512),
                record.get("height", 512),
                record.get("steps", 18),
                float(record.get("elapsed_seconds", 0.0)),
                float(record.get("compute_work_units", 1.0)),
                float(record.get("savings_percent", 0.0)),
                record.get("model", "stable-diffusion-v1-5"),
                record.get("provider", "automatic1111"),
                record.get("status", "success"),
                record.get("image_url", ""),
            ),
        )
        conn.commit()


def get_generation_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent real generation records, ordered newest first."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT job_id, timestamp, prompt, negative_prompt,
                   inferred_purpose, recommended_tier, selected_tier,
                   tier_overridden, width, height, steps,
                   elapsed_seconds, compute_work_units, savings_percent,
                   model, provider, status, image_url
            FROM generation_records
            WHERE status = 'success'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def clear_generation_history() -> None:
    """Deletes all persistent generation records."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM generation_records")
        conn.commit()


def get_real_analytics() -> Dict[str, Any]:
    """Computes genuine aggregate metrics strictly from real historical generations."""
    init_db()
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM generation_records WHERE status = 'success'")
        total = cursor.fetchone()["total"]

        if total == 0:
            return {
                "total_generations": 0,
                "eco_count": 0,
                "standard_count": 0,
                "high_count": 0,
                "overridden_count": 0,
                "total_compute_units": 0.0,
                "baseline_units": 0.0,
                "units_saved": 0.0,
                "overall_savings_percent": 0.0,
                "avg_elapsed_seconds": 0.0,
                "is_empty": True,
            }

        cursor.execute("""
            SELECT 
                SUM(CASE WHEN selected_tier = 'eco' THEN 1 ELSE 0 END) as eco_cnt,
                SUM(CASE WHEN selected_tier = 'standard' THEN 1 ELSE 0 END) as std_cnt,
                SUM(CASE WHEN selected_tier IN ('high', 'high_quality', 'hd') THEN 1 ELSE 0 END) as high_cnt,
                SUM(CASE WHEN tier_overridden = 1 THEN 1 ELSE 0 END) as over_cnt,
                SUM(compute_work_units) as total_units,
                AVG(elapsed_seconds) as avg_time
            FROM generation_records
            WHERE status = 'success'
        """)
        row = cursor.fetchone()

        eco_count = row["eco_cnt"] or 0
        standard_count = row["std_cnt"] or 0
        high_count = row["high_cnt"] or 0
        overridden_count = row["over_cnt"] or 0
        total_units = round(float(row["total_units"] or 0.0), 3)
        avg_time = round(float(row["avg_time"] or 0.0), 2)

        # Baseline High tier reference units: 1.0 unit per generation
        baseline_units = float(total)
        units_saved = round(max(0.0, baseline_units - total_units), 3)
        savings_pct = round((units_saved / baseline_units) * 100.0, 1) if baseline_units > 0 else 0.0

        return {
            "total_generations": total,
            "eco_count": eco_count,
            "standard_count": standard_count,
            "high_count": high_count,
            "overridden_count": overridden_count,
            "total_compute_units": total_units,
            "baseline_units": baseline_units,
            "units_saved": units_saved,
            "overall_savings_percent": savings_pct,
            "avg_elapsed_seconds": avg_time,
            "is_empty": False,
        }
