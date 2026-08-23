from io import BytesIO

from PIL import Image


def make_test_jpeg(*, width: int = 600, height: int = 600, color=(128, 128, 128), textured: bool = True) -> bytes:
    """A real, valid, in-memory JPEG - not a mock. `textured=True` (the
    default) adds a simple checkerboard pattern so the image has genuine
    edges/variance and is correctly judged NOT blurry by the real quality
    heuristic - a perfectly flat solid color has zero texture and is
    correctly flagged "too_blurry" (this is the heuristic working
    correctly, not a bug - see test_quality_flags_flat_image_as_blurry).
    Pass textured=False when a test specifically wants a flat, low-detail
    image."""
    img = Image.new("RGB", (width, height), color=color)
    if textured:
        pixels = img.load()
        block = max(4, min(width, height) // 40)
        for y in range(height):
            for x in range(width):
                if (x // block + y // block) % 2 == 0:
                    r, g, b = color
                    pixels[x, y] = (min(255, r + 40), min(255, g + 40), min(255, b + 40))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_test_png(*, width: int = 600, height: int = 600, color=(200, 50, 50)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def valid_photo_session_payload(crop_cycle_id: str, **overrides):
    payload = {"crop_cycle_id": crop_cycle_id, "label": "Leaf check"}
    payload.update(overrides)
    return payload
