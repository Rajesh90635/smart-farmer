"""
TesseractOCRProvider: a genuinely working implementation, not a
placeholder. Every extraction step is a deterministic, disclosed
heuristic - never a machine-learned guess dressed up as certainty.

Amount extraction: regex-matches currency-like number patterns (Rs/INR
prefixed, or plain decimal numbers) and picks the LARGEST match - the
common convention that an invoice/receipt's total is its largest number.
A real, disclosed limitation: it will be wrong for invoices with an
unusual layout, which is exactly why farmer confirmation is mandatory
before this ever reaches the financial ledger.

Date extraction: regex-matches common DD/MM/YYYY-style patterns, takes
the first match. Also a disclosed heuristic, not authoritative.

Vendor name extraction: takes the first few substantial (letter-
containing) words of OCR text - receipts conventionally have the shop/
vendor name at the top. Weak heuristic, disclosed.

Confidence: computed from Tesseract's own real per-word confidence
scores (image_to_data) - never fabricated. Thresholds are configurable,
explicitly disclosed as placeholders pending real-world validation.
"""
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import pytesseract
from PIL import Image
from pytesseract import Output

from app.core.config import Settings
from app.services.ocr.ocr_provider import OCRConfidenceLevel, OCRExtractionResult, OCRProvider

_AMOUNT_PATTERN = re.compile(r"(?:rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_BARE_NUMBER_PATTERN = re.compile(r"\b(\d{2,7}(?:\.\d{1,2})?)\b")
_DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b"),
    re.compile(r"\b(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\b"),
]


class TesseractOCRProvider(OCRProvider):
    @property
    def provider_name(self) -> str:
        return "tesseract"

    def is_ready(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_invoice_data(self, image_bytes: bytes, settings: Settings | None = None) -> OCRExtractionResult:
        if not self.is_ready():
            return OCRExtractionResult(available=False, unavailable_reason="OCR engine is not available on this server.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("L")
        except Exception:
            return OCRExtractionResult(available=False, unavailable_reason="Could not read this image file.")

        try:
            data = pytesseract.image_to_data(image, output_type=Output.DICT)
        except Exception:
            return OCRExtractionResult(available=False, unavailable_reason="Text extraction failed for this image.")

        words = []
        confidences = []
        for text, conf in zip(data.get("text", []), data.get("conf", [])):
            if text.strip():
                words.append(text.strip())
                try:
                    conf_value = float(conf)
                    if conf_value >= 0:
                        confidences.append(conf_value)
                except (TypeError, ValueError):
                    pass

        raw_text = " ".join(words)
        mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        confidence = self._classify_confidence(mean_confidence, settings)

        return OCRExtractionResult(
            available=True,
            raw_text=raw_text if raw_text else None,
            extracted_amount=self._extract_amount(raw_text),
            extracted_date=self._extract_date(raw_text),
            extracted_vendor_name=self._extract_vendor_name(words),
            confidence=confidence,
        )

    @staticmethod
    def _classify_confidence(mean_confidence: float, settings: Settings | None) -> OCRConfidenceLevel:
        high_threshold = settings.ocr_high_confidence_mean_word_score if settings else 75.0
        medium_threshold = settings.ocr_medium_confidence_mean_word_score if settings else 45.0
        if mean_confidence >= high_threshold:
            return OCRConfidenceLevel.HIGH
        if mean_confidence >= medium_threshold:
            return OCRConfidenceLevel.MEDIUM
        return OCRConfidenceLevel.LOW

    @staticmethod
    def _extract_amount(raw_text: str) -> Decimal | None:
        if not raw_text:
            return None
        currency_matches = _AMOUNT_PATTERN.findall(raw_text)
        candidates = currency_matches if currency_matches else _BARE_NUMBER_PATTERN.findall(raw_text)
        if not candidates:
            return None
        try:
            parsed = [Decimal(c.replace(",", "")) for c in candidates]
        except InvalidOperation:
            return None
        return max(parsed) if parsed else None

    @staticmethod
    def _extract_date(raw_text: str) -> date | None:
        if not raw_text:
            return None
        for pattern in _DATE_PATTERNS:
            match = pattern.search(raw_text)
            if match:
                groups = [int(g) for g in match.groups()]
                try:
                    if groups[0] > 31:
                        return date(groups[0], groups[1], groups[2])
                    return date(groups[2], groups[1], groups[0])
                except ValueError:
                    continue
        return None

    @staticmethod
    def _extract_vendor_name(words: list[str]) -> str | None:
        letters_only = [w for w in words if re.search(r"[A-Za-z]{3,}", w)]
        if not letters_only:
            return None
        return " ".join(letters_only[:4])
