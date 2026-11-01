"""Safe URL ingestion service with strict SSRF protection and content extraction."""

import ipaddress
import re
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from questiontrail.domain.models import (
    Source,
    SourceType,
    SourceAuthority,
    ExtractionStatus,
    utc_now,
)
from questiontrail.services.canonical import compute_content_hash

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_TIMEOUT_SECONDS = 10.0
USER_AGENT = "QuestionTrail/0.1.0 (+https://github.com/questiontrail; research-bot)"


class IngestionError(Exception):
    """Base exception for source ingestion errors."""
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_url_safety(url_str: str) -> str:
    """Validate URL format and ensure it does not resolve to private/local/SSRF targets.

    Raises IngestionError if the URL is invalid or targets a forbidden network destination.
    Returns normalized clean URL.
    """
    if not url_str or not isinstance(url_str, str):
        raise IngestionError("URL cannot be empty")

    url_str = url_str.strip()
    try:
        parsed = urlparse(url_str)
    except Exception as exc:
        raise IngestionError(f"Malformed URL: {exc}") from exc

    if parsed.scheme.lower() not in ("http", "https"):
        raise IngestionError("Invalid URL scheme. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise IngestionError("URL must contain a valid hostname.")

    # Block localhost string literals directly
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise IngestionError(f"Access to local/private destination '{hostname}' is forbidden.")

    # Resolve IP address to prevent DNS rebinding or private IP access
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise IngestionError(f"Failed to resolve host '{hostname}': {exc}") from exc

    if not addr_info:
        raise IngestionError(f"Could not resolve host '{hostname}' to any IP address.")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise IngestionError(
                f"Destination '{hostname}' resolves to private/restricted IP ({ip_str}), which is blocked for security."
            )

    return url_str


def assess_domain_authority(url_str: str) -> SourceAuthority:
    """Classify authority based on top-level domain and patterns."""
    parsed = urlparse(url_str)
    host = (parsed.hostname or "").lower()
    if host.endswith(".gov") or host.endswith(".gov.in") or host.endswith(".nic.in"):
        return SourceAuthority.primary_official
    if host.endswith(".edu") or host.endswith(".edu.in") or host.endswith(".ac.in") or host.endswith(".org"):
        return SourceAuthority.secondary_authoritative
    return SourceAuthority.third_party


def extract_metadata_and_text(html_content: str, url: str) -> tuple[str, str | None, str]:
    """Extract clean title, publication date (if present), and readable body text.

    Returns:
        (title, publication_date_iso_or_none, body_text)
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe"]):
        tag.decompose()

    # 1. Title extraction
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = str(og_title["content"]).strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.h1:
        title = soup.h1.get_text().strip()

    if not title:
        parsed = urlparse(url)
        title = f"Document at {parsed.netloc}{parsed.path}"

    # 2. Date extraction (best-effort heuristic)
    pub_date: str | None = None
    date_meta = (
        soup.find("meta", property="article:published_time")
        or soup.find("meta", attrs={"name": "article:published_time"})
        or soup.find("meta", attrs={"name": "date"})
        or soup.find("meta", attrs={"name": "pubdate"})
        or soup.find("meta", property="og:published_time")
    )
    if date_meta and date_meta.get("content"):
        raw_date = str(date_meta["content"]).strip()
        # Grab YYYY-MM-DD prefix if present
        m = re.match(r"(\d{4}-\d{2}-\d{2})", raw_date)
        if m:
            pub_date = m.group(1)
        else:
            pub_date = raw_date[:10]
    else:
        # Check <time datetime="...">
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            raw_datetime = str(time_tag["datetime"]).strip()
            m = re.match(r"(\d{4}-\d{2}-\d{2})", raw_datetime)
            if m:
                pub_date = m.group(1)

    # 3. Clean text extraction
    # Prefer <main> or <article> if available
    main_container = soup.find("main") or soup.find("article") or soup.body or soup
    text = main_container.get_text(separator="\n", strip=True)
    # Collapse excess empty lines
    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    body_text = "\n".join(cleaned_lines)

    return title, pub_date, body_text


def fetch_and_extract_url(
    url_str: str,
    client: httpx.Client | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Source:
    """Safely fetch public URL and extract Source with provenance and content hash.

    Raises IngestionError if safety checks, network request, or extraction fail.
    """
    safe_url = validate_url_safety(url_str)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    http_client = client or httpx.Client(timeout=timeout, follow_redirects=True)
    try:
        response = http_client.get(safe_url, headers=headers)
    except httpx.TimeoutException as exc:
        raise IngestionError(f"Connection to '{safe_url}' timed out after {timeout} seconds.") from exc
    except httpx.RequestError as exc:
        raise IngestionError(f"Network error while fetching '{safe_url}': {exc}") from exc

    if response.status_code >= 400:
        raise IngestionError(
            f"Failed to fetch '{safe_url}': HTTP {response.status_code} ({response.reason_phrase}).",
            status_code=response.status_code,
        )

    # Check content size
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise IngestionError(
            f"Content length exceeds maximum limit of {MAX_RESPONSE_BYTES // (1024*1024)}MB."
        )

    # Content-type check
    ctype = response.headers.get("content-type", "").lower()
    if "text" not in ctype and "html" not in ctype and "xml" not in ctype and "json" not in ctype:
        raise IngestionError(f"Unsupported content type '{ctype}'. Expected HTML or text document.")

    title, pub_date, body_text = extract_metadata_and_text(response.text, safe_url)
    if not body_text:
        raise IngestionError(f"No readable text content could be extracted from '{safe_url}'.")

    content_hash = compute_content_hash(body_text)
    authority = assess_domain_authority(safe_url)
    source_id = f"src-url-{content_hash[:8]}"

    return Source(
        id=source_id,
        title=title,
        url=safe_url,
        type=SourceType.webpage,
        authority=authority,
        publication_date=pub_date,
        cycle_or_version=None,
        retrieved_at=utc_now(),
        extraction_status=ExtractionStatus.success,
        content_hash=content_hash,
        raw_content=body_text,
        metadata={
            "http_status": response.status_code,
            "content_length": len(body_text),
            "content_type": ctype,
        },
    )
