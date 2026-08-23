"""
Single switch point for the OCR provider - mirrors get_model_provider
(Prompt 6), get_weather_provider (Prompt 7), and get_ai_provider (Prompt
11) exactly. Unlike those, this one returns a genuinely working
implementation by default, since Tesseract OCR is free, local, and
actually installed in every environment this app is deployed to (a
system dependency, not a cloud API key) - verified directly in this
sandbox before relying on it.
"""
from functools import lru_cache

from app.services.ocr.ocr_provider import OCRProvider
from app.services.ocr.tesseract_ocr_provider import TesseractOCRProvider


@lru_cache
def get_ocr_provider() -> OCRProvider:
    return TesseractOCRProvider()
