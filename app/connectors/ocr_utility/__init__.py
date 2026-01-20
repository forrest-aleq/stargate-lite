"""
OCR/Document Intelligence utility for Stargate Lite
Uses deepdoctection for basic extraction, Gemini Flash for complex documents
https://github.com/deepdoctection/deepdoctection

Per architecture decision: Option B (internal utility) for v1
Gemini 3 Flash added for table extraction and complex document understanding
"""

from .gemini import GeminiMixin


class OCRUtility(GeminiMixin):
    """
    Document Intelligence utility using deepdoctection + Gemini Flash.

    Inherits from GeminiMixin which inherits from DeepDocMixin
    which inherits from OCRBase.
    """

    pass


__all__ = ["OCRUtility"]
