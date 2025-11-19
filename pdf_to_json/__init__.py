"""
PDF to JSON Converter Module

A module to convert PDF files to JSON format, preserving text and image positions.
Supports AI-powered image analysis using Qwen Vision model.
"""

from .converter import PDFToJSONConverter

__version__ = "1.0.0"
__all__ = ["PDFToJSONConverter"]
