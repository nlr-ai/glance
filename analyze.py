"""GLANCE Analyze — DOI/URL extraction utilities (V2 placeholder).

For now, only handles direct image upload. DOI and URL extraction
will be added in a future iteration.
"""

import io
import logging

logger = logging.getLogger(__name__)


def extract_ga_from_pdf(pdf_bytes: bytes) -> bytes | None:
    """Extract the largest image from a PDF file.

    Uses PyMuPDF (fitz) if available, otherwise returns None.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed — cannot extract images from PDF.")
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        best_image = None
        best_size = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if base_image:
                    img_bytes = base_image["image"]
                    if len(img_bytes) > best_size:
                        best_size = len(img_bytes)
                        best_image = img_bytes

        doc.close()
        return best_image
    except Exception as e:
        logger.error(f"PDF image extraction failed: {e}")
        return None


def extract_ga_from_url(url: str) -> bytes | None:
    """Download a GA image from a URL.

    Simple HTTP GET. Returns image bytes or None on failure.
    V2 will add DOI resolution, publisher-specific GA extraction, etc.
    """
    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GLANCE-SciSense/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "image" in content_type or url.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                return resp.read()
            else:
                logger.warning(f"URL does not appear to be an image: {content_type}")
                return None
    except Exception as e:
        logger.error(f"URL download failed: {e}")
        return None
