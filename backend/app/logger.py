"""
logger.py — Logger centralisé pour ambient-task-listener.

Utilisation dans les modules :
    from app.logger import get_logger
    logger = get_logger(__name__)
"""
from __future__ import annotations

import logging

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Configure le handler racine "ambient" une seule fois
_root_logger = logging.getLogger("ambient")

if not _root_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FMT))
    _root_logger.addHandler(_handler)
    _root_logger.setLevel(logging.DEBUG)
    # Empêche la propagation vers le root logger de Python
    _root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger enfant du logger racine 'ambient'.

    Exemple :
        logger = get_logger(__name__)   # → "ambient.app.storage"
    """
    if name.startswith("ambient"):
        return logging.getLogger(name)
    return logging.getLogger(f"ambient.{name}")
