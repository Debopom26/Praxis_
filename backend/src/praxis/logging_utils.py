"""Allowlisted structured operational logs; never include request bodies or credentials."""

import json
import logging
from datetime import datetime, timezone


class SafeFormatter(logging.Formatter):
    def format(self, record):
        fields = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for key in ["request_id", "session_id", "window_id", "module", "status", "latency_ms"]:
            if hasattr(record, key):
                fields[key] = getattr(record, key)
        return json.dumps(fields, ensure_ascii=True)


def configure_logging():
    logger = logging.getLogger("praxis")
    if not any(isinstance(handler.formatter, SafeFormatter) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(SafeFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
