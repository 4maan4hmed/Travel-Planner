"""Configure LangSmith tracing for LangGraph agent runs."""

from __future__ import annotations

import logging
import os

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_configured = False


def configure_langsmith() -> bool:
    """Apply LangSmith settings to the process env so LangChain/LangGraph auto-trace.

    Returns True when tracing is enabled.
    """
    global _configured
    if _configured:
        return os.getenv("LANGSMITH_TRACING", "").lower() == "true"

    settings = get_settings()
    _configured = True

    if not settings.langsmith_tracing:
        os.environ.setdefault("LANGSMITH_TRACING", "false")
        return False

    if not settings.langsmith_api_key:
        logger.warning(
            "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is missing; "
            "agent traces will not be sent."
        )
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    logger.info(
        "LangSmith tracing enabled (project=%s)",
        settings.langsmith_project,
    )
    return True
