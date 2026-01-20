"""
Base class for OCR utility with initialization.
"""

import os
from typing import Any

from app.errors import InternalStargateError
from app.logging_config import get_logger

logger = get_logger(__name__)

# deepdoctection imports
try:
    from deepdoctection import analyzer

    DEEPDOCTECTION_AVAILABLE = True
except ImportError:
    analyzer = None
    DEEPDOCTECTION_AVAILABLE = False

# Gemini Flash imports
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False


class OCRBase:
    """Document Intelligence utility base class with lazy initialization."""

    def __init__(self) -> None:
        self.analyzer: Any = None
        self._initialized = False
        self._gemini_initialized = False
        self._gemini_model: Any = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of deepdoctection analyzer"""
        if self._initialized:
            return

        if not DEEPDOCTECTION_AVAILABLE:
            raise InternalStargateError(
                "deepdoctection library not installed",
                details={
                    "service": "ocr",
                    "install_command": "pip install deepdoctection[source-pt]",
                },
            )

        # Initialize analyzer with default configuration
        # This uses Tesseract for OCR + layout detection models
        try:
            self.analyzer = analyzer.Analyzer()
            self._initialized = True
        except Exception as e:
            raise InternalStargateError(
                f"Failed to initialize deepdoctection analyzer: {e!s}",
                details={"service": "ocr", "error": str(e)},
            ) from e

    def _ensure_gemini_initialized(self) -> None:
        """Lazy initialization of Gemini Flash model"""
        if self._gemini_initialized:
            return

        if not GEMINI_AVAILABLE:
            raise InternalStargateError(
                "google-generativeai library not installed",
                details={"service": "ocr", "install_command": "pip install google-generativeai"},
            )

        api_key = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise InternalStargateError(
                "GOOGLE_AI_API_KEY or GEMINI_API_KEY not configured", details={"service": "ocr"}
            )

        try:
            genai.configure(api_key=api_key)
            # Use Gemini 3 Flash for speed and cost efficiency
            self._gemini_model = genai.GenerativeModel("gemini-3-flash-preview")
            self._gemini_initialized = True
        except Exception as e:
            raise InternalStargateError(
                f"Failed to initialize Gemini: {e!s}", details={"service": "ocr", "error": str(e)}
            ) from e
