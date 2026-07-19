"""Central logging setup — replaces scattered ``print()`` calls."""
from __future__ import annotations

import logging
import os

_CONFIGURED = False


def setup_logging(level: str | None = None) -> None:
    """Configure root logging once. Level from arg or the LOG_LEVEL env var (default INFO)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, lvl, logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Get a module logger, ensuring logging is configured."""
    setup_logging()
    return logging.getLogger(name)
