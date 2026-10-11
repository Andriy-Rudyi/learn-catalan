"""Catalan conjugation: validated input, corrected verbecc output."""

from flaskblog.conjugation.service import (
    ConjugationResult,
    ConjugationService,
    get_service,
)

__all__ = ["ConjugationResult", "ConjugationService", "get_service"]
