"""
Automatic SQLite backups.

Your entire job hunt lives in one SQLite file — this makes a dated copy in
``backups/`` at most once per day (called on app start) and prunes old ones.
No-op for non-SQLite databases.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.logging_config import get_logger
from db.session import DB_URL

log = get_logger(__name__)

BACKUP_DIR = Path("backups")


def backup_database(max_backups: int = 14) -> Optional[Path]:
    """Copy the SQLite DB to backups/<name>-YYYY-MM-DD.db (once per day).

    Returns the backup path if one was made, else None. Never raises —
    a failed backup must not stop the app.
    """
    try:
        if not DB_URL.startswith("sqlite"):
            return None
        db_path = Path(DB_URL.replace("sqlite:///", "", 1))
        if not db_path.exists() or db_path.stat().st_size == 0:
            return None

        BACKUP_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d")
        target = BACKUP_DIR / f"{db_path.stem}-{stamp}.db"
        if target.exists():
            return None  # already backed up today

        shutil.copy2(db_path, target)
        log.info("database backed up to %s", target)

        # Prune: keep the newest max_backups
        backups = sorted(BACKUP_DIR.glob(f"{db_path.stem}-*.db"), reverse=True)
        for old in backups[max_backups:]:
            old.unlink(missing_ok=True)

        return target
    except Exception as exc:
        log.warning("database backup failed: %s", exc)
        return None
