"""Extract Graphical Abstract images from journal websites.

Given a paper URL (or DOI), fetches the page, locates the GA image
using journal-specific CSS selectors or og:image fallback, downloads it,
and returns image bytes + metadata (title, authors, journal, DOI).

Integration:
    - Calls vision_scorer.analyze_ga_image() for GLANCE scoring
    - Calls archetype.classify_from_vision_metadata() for archetype
    - Extracted GAs go to ga_library/ with JSON sidecar
"""

import re
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Minimum image size in bytes to be considered a real GA (not an icon/logo)
MIN_IMAGE_SIZE = 10_000  # 10 KB

# ── Journal-specific CSS selectors ────────────────────────────────────────

GA_SELECTORS = {
    "sciencedirect.com": "figure.graphical-abstract img, .abstract-graphical img",
    "mdpi.com": ".html-ga img, .graphical-abstract img",
    "nature.com": None,  # og:image fallback
    "pnas.org": ".fig:first-child img",
    "plos.org": ".figure:first-child img",
    "frontiersin.org": ".AbstractSummary img",
    "onlinelibrary.wiley.com": ".article__graphicalAbstract img",
    "cell.com": ".graphical-abstract img, .fx1 img",
    "bmj.com": ".graphic-wrap img",
    "thelancet.com": ".graphical-abstract img",
}

# ── DOI resolution ────────────────────────────────────────────────────────

DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s]+')


def resolve_doi(url_or_doi: str) -> str | None:
    """Extract or resolve a DOI to a landing page URL.

    If the input is already a URL, tries to extract DOI from it.
    If the input is a DOI, resolves via doi.org redirect.
    """
    # If it looks like a bare DOI
    if url_or_doi.startswith("10."):
        return f"https://doi.org/{url_or_doi}"

    # If it's a doi.org URL, return as-is (will redirect)
    if "doi.org/" in url_or_doi:
        return url_or_doi

    # Try to extract DOI from URL path
    match = DOI_PATTERN.search(url_or_doi)
    if match:
        return f"https://doi.org/{match.group()}"

    return None


def _get_domain(url: str) -> str:
    """Extract the registrable domain from a URL."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    # Get last two parts (e.g., nature.com from www.nature.com)
    parts = hostname.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname


# ── HTML fetching & parsing ───────────────────────────────────────────────

def _fetch_page(url: str, timeout: int = 30) -> tuple[str, str]:
    """Fetch a URL, following redirects. Returns (final_url, html).

    Raises RuntimeError on failure.
    """
    try:
        import requests
    except ImportError:
        raise RuntimeError(
            "requests package required. Install with: pip install requests"
        )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp.url, resp.text


def _parse_html(html: str):
    """Parse HTML with BeautifulSoup. Returns soup object."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise RuntimeError(
            "beautifulsoup4 package required. Install with: pip install beautifulsoup4"
        )
    return BeautifulSoup(html, "html.parser")


def _extract_metadata(soup, url: str) -> dict:
    """Extract paper metadata from HTML meta tags."""
    meta = {
        "source_url": url,
        "title": None,
        "authors": None,
        "journal": None,
        "doi": None,
        "content_type": None,
    }

    # Title: try citation_title first, then og:title, then <title>
    for selector in [
        {"name": "citation_title"},
        {"property": "og:title"},
        {"name": "dc.title"},
    ]:
        tag = soup.find("meta", attrs=selector)
        if tag and tag.get("content"):
            meta["title"] = tag["content"].strip()
            break
    if not meta["title"]:
        title_tag = soup.find("title")
        if title_tag:
            meta["title"] = title_tag.get_text(strip=True)

    # Authors
    author_tags = soup.find_all("meta", attrs={"name": "citation_author"})
    if author_tags:
        meta["authors"] = ", ".join(
            t["content"].strip() for t in author_tags if t.get("content")
        )

    # Journal
    journal_tag = soup.find("meta", attrs={"name": "citation_journal_title"})
    if journal_tag and journal_tag.get("content"):
        meta["journal"] = journal_tag["content"].strip()

    # DOI
    doi_tag = soup.find("meta", attrs={"name": "citation_doi"})
    if doi_tag and doi_tag.get("content"):
        meta["doi"] = doi_tag["content"].strip()
    else:
        # Try to find DOI in page text
        match = DOI_PATTERN.search(str(soup))
        if match:
            meta["doi"] = match.group()

    return meta


def _find_ga_image_url(soup, url: str) -> str | None:
    """Find GA image URL using journal-specific selectors, then fallback."""
    domain = _get_domain(url)

    # Try journal-specific selectors
    selector = GA_SELECTORS.get(domain)
    if selector is not None:
        imgs = soup.select(selector)
        for img in imgs:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if src:
                full_url = urljoin(url, src)
                logger.info(f"Found GA via selector '{selector}': {full_url}")
                return full_url

    # Fallback 1: look for elements with "graphical" or "abstract" in
    # class/id near an img
    for container in soup.find_all(
        attrs={"class": re.compile(r'graphical|abstract', re.I)}
    ):
        img = container.find("img")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                full_url = urljoin(url, src)
                logger.info(f"Found GA via class pattern: {full_url}")
                return full_url

    # Fallback 2: og:image meta tag
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        full_url = og_img["content"]
        if not full_url.startswith("http"):
            full_url = urljoin(url, full_url)
        logger.info(f"Found GA via og:image: {full_url}")
        return full_url

    # Fallback 3: twitter:image
    tw_img = soup.find("meta", attrs={"name": "twitter:image"})
    if tw_img and tw_img.get("content"):
        full_url = tw_img["content"]
        if not full_url.startswith("http"):
            full_url = urljoin(url, full_url)
        logger.info(f"Found GA via twitter:image: {full_url}")
        return full_url

    return None


def _download_image(url: str, timeout: int = 30) -> tuple[bytes, str]:
    """Download image bytes. Returns (bytes, content_type)."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests package required")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")

    # Validate it's actually an image
    if not content_type.startswith("image/"):
        # Check magic bytes
        data = resp.content
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            content_type = "image/png"
        elif data[:3] == b'\xff\xd8\xff':
            content_type = "image/jpeg"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            content_type = "image/webp"
        elif data[:4] == b'GIF8':
            content_type = "image/gif"
        else:
            raise ValueError(
                f"URL does not serve an image (Content-Type: {content_type})"
            )

    return resp.content, content_type


def _validate_image(image_bytes: bytes) -> bool:
    """Validate that image bytes represent a real image of sufficient size."""
    if len(image_bytes) < MIN_IMAGE_SIZE:
        logger.warning(
            f"Image too small ({len(image_bytes)} bytes < {MIN_IMAGE_SIZE})"
        )
        return False

    # Try to verify with Pillow if available
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if w < 100 or h < 100:
            logger.warning(f"Image too small: {w}x{h} pixels")
            return False
        logger.info(f"Image validated: {w}x{h}, {len(image_bytes)} bytes")
        return True
    except ImportError:
        # Pillow not available, trust the size check
        return True
    except Exception as e:
        logger.warning(f"Image validation failed: {e}")
        return False


# ── Public API ────────────────────────────────────────────────────────────

def extract_ga_from_url(url: str) -> dict | None:
    """Extract Graphical Abstract image from a paper URL.

    Args:
        url: URL of a paper page, or a DOI (bare or as doi.org URL)

    Returns:
        dict with keys:
            - image_bytes: raw image bytes
            - metadata: dict with title, authors, journal, doi, source_url, content_type
        or None if no GA found.
    """
    # Resolve DOI if needed
    doi_url = resolve_doi(url)
    if doi_url and doi_url != url:
        logger.info(f"Resolved DOI URL: {doi_url}")
        url = doi_url

    # Fetch the page
    logger.info(f"Fetching: {url}")
    try:
        final_url, html = _fetch_page(url)
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

    if final_url != url:
        logger.info(f"Redirected to: {final_url}")

    # Parse HTML
    soup = _parse_html(html)

    # Extract metadata
    metadata = _extract_metadata(soup, final_url)

    # Find GA image URL
    img_url = _find_ga_image_url(soup, final_url)
    if img_url is None:
        logger.info(f"No GA image found at {final_url}")
        return None

    # Download the image
    try:
        image_bytes, content_type = _download_image(img_url)
    except Exception as e:
        logger.error(f"Failed to download image {img_url}: {e}")
        return None

    metadata["content_type"] = content_type
    metadata["image_url"] = img_url

    # Validate
    if not _validate_image(image_bytes):
        logger.warning(f"Image validation failed for {img_url}")
        return None

    return {
        "image_bytes": image_bytes,
        "metadata": metadata,
    }
