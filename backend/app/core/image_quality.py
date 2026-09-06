"""
Basic technical image-quality heuristics (Requirement 7).

HARD RULE: this module never claims anything about disease, pests, or
plant health. Its only vocabulary is technical: too dark, too bright, too
blurry (and, D30-05/D30-06, possibly the same subject already captured, or
captured a long time before upload). The farmer-facing message is always a
retake instruction, never a diagnosis - see docs/IMAGE_VALIDATION.md.
"""
from dataclasses import dataclass, field
from datetime import datetime

from PIL import Image, ImageFilter, ImageStat

from app.core.config import Settings


@dataclass(frozen=True)
class QualityCheckResult:
    accepted: bool
    reasons: list[str] = field(default_factory=list)  # e.g. ["too_dark", "too_blurry"]


def check_quality(image: Image.Image, settings: Settings) -> QualityCheckResult:
    reasons: list[str] = []

    grayscale = image.convert("L")

    brightness = ImageStat.Stat(grayscale).mean[0]
    if brightness < settings.photo_quality_min_mean_brightness:
        reasons.append("too_dark")
    elif brightness > settings.photo_quality_max_mean_brightness:
        reasons.append("too_bright")

    blur_variance = _laplacian_variance(grayscale)
    if blur_variance < settings.photo_quality_min_blur_variance:
        reasons.append("too_blurry")

    return QualityCheckResult(accepted=len(reasons) == 0, reasons=reasons)


def _laplacian_variance(grayscale: Image.Image) -> float:
    """
    A lightweight blur proxy: apply an edge-detection kernel (Pillow's
    built-in FIND_EDGES, a Laplacian-like filter) and measure the variance
    of the result. A sharp, in-focus image has strong edges and high
    variance; a blurry image's edges are washed out, giving low variance.

    The 2px border is cropped out before measuring variance - convolution
    edge-handling produces a spurious high-contrast ring around the
    entire image (verified empirically: a perfectly flat, featureless
    test image showed variance ~108 instead of ~0 before this crop, which
    would have made the heuristic nearly useless - a genuinely blurry
    photo could pass purely on border artifacts). This is a real
    correctness fix, found by testing with an actual flat-color image,
    not a hypothetical.
    """
    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    width, height = edges.size
    if width > 4 and height > 4:
        edges = edges.crop((2, 2, width - 2, height - 2))
    stat = ImageStat.Stat(edges)
    # ImageStat variance = stddev^2 per band; single band since grayscale.
    return stat.var[0]


def compute_average_hash(image: Image.Image) -> str:
    """D30-05 (docs/audit/FINAL_CANONICAL_group_B.md): a standard
    perceptual "average hash" (aHash) - downscale to 8x8 grayscale, then
    one bit per pixel for whether it's at/above the mean. Two photos of
    the genuinely same subject produce near-identical hashes (small
    Hamming distance) even with minor recompression/lighting differences;
    two unrelated photos produce hashes that differ in roughly half their
    bits. Not cryptographic, not unique per pixel - a similarity signal
    only, matched via hamming_distance() below."""
    small = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    mean = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= mean else "0" for p in pixels)
    return f"{int(bits, 2):016x}"


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Count of differing bits between two compute_average_hash() outputs
    - 0 means pixel-identical downscaled images, 32 (of 64) is the
    expected distance for two unrelated photos."""
    return bin(int(hash_a, 16) ^ int(hash_b, 16)).count("1")


def is_capture_stale(capture_timestamp: datetime | None, upload_timestamp: datetime, settings: Settings) -> bool:
    """D30-06 (docs/audit/FINAL_CANONICAL_group_B.md): flags a photo whose
    device-reported capture time is more than the configured threshold
    before it was actually uploaded. Never fabricated: a photo with no
    capture_timestamp (an older client that doesn't send it yet) is never
    flagged - there is no real data to judge staleness from."""
    if capture_timestamp is None:
        return False
    age_days = (upload_timestamp - capture_timestamp).total_seconds() / 86400
    return age_days > settings.photo_stale_capture_days
