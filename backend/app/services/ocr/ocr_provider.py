"""
OCRProvider: the abstraction for invoice text extraction, mirroring the
EXACT same pattern already established for ModelProvider (Prompt 6),
WeatherProvider (Prompt 7), and AIProvider (Prompt 11) - business code
depends only on this interface, never on a specific OCR engine directly.

Unlike those three providers, this one has a genuinely WORKING default
implementation (see tesseract_ocr_provider.py) rather than a
"not configured" placeholder - Tesseract OCR is free, open-source
(Apache 2.0), and runs fully locally/offline, and it's actually installed
and functional in this environment (verified directly: tesseract
--version and import pytesseract both succeed here, not assumed).

THE ABSOLUTE SAFETY RULE: every extracted field is a BEST-GUESS heuristic,
never treated as ground truth. `confidence` is a REAL score computed from
Tesseract's own per-word confidence output - never fabricated. No
extracted value is ever written to the financial ledger automatically -
only an explicit farmer confirmation creates a real LedgerEntry.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class OCRConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class OCRExtractionResult:
    available: bool
    raw_text: str | None = None
    extracted_amount: Decimal | None = None
    extracted_date: date | None = None
    extracted_vendor_name: str | None = None
    confidence: OCRConfidenceLevel | None = None
    unavailable_reason: str | None = None


class OCRProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def is_ready(self) -> bool: ...

    @abstractmethod
    def extract_invoice_data(self, image_bytes: bytes, settings=None) -> OCRExtractionResult:
        """Never raises for a bad/unreadable image - returns
        available=False with unavailable_reason instead, matching the
        same convention as every other provider abstraction here.
        `settings` (app.core.config.Settings) is accepted so confidence
        thresholds stay configurable - typed loosely here (not imported)
        to avoid a circular import between this low-level provider
        module and app.core.config."""
