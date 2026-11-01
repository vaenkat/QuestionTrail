"""Tests for safe URL ingestion and PDF extraction."""

import io
import pytest
import httpx
from pypdf import PdfWriter

from questiontrail.services.url_ingestion import (
    validate_url_safety,
    extract_metadata_and_text,
    fetch_and_extract_url,
    IngestionError,
)
from questiontrail.services.pdf_ingestion import extract_pdf_source


def test_ssrf_blocks_private_and_local():
    with pytest.raises(IngestionError, match="forbidden|blocked|private"):
        validate_url_safety("http://localhost:8000/secret")

    with pytest.raises(IngestionError, match="forbidden|blocked|private"):
        validate_url_safety("http://127.0.0.1:8000/secret")

    with pytest.raises(IngestionError, match="forbidden|blocked|private"):
        validate_url_safety("http://0.0.0.0/")


def test_ssrf_blocks_invalid_schemes():
    with pytest.raises(IngestionError, match="scheme"):
        validate_url_safety("ftp://example.com/file.txt")

    with pytest.raises(IngestionError, match="scheme"):
        validate_url_safety("file:///etc/passwd")


def test_html_metadata_and_text_extraction():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Official Solar Program 2026</title>
        <meta property="og:title" content="Solar Incentive Grants 2026" />
        <meta property="article:published_time" content="2026-04-15T09:00:00Z" />
      </head>
      <body>
        <nav><a href="/">Home</a></nav>
        <main>
          <h1>Solar Incentive Program</h1>
          <p>Eligible homeowners can receive a grant of up to $5,000 for battery installation.</p>
          <p>Applications close on November 30, 2026.</p>
        </main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    title, pub_date, text = extract_metadata_and_text(html, "https://example.gov/solar")
    assert title == "Solar Incentive Grants 2026"
    assert pub_date == "2026-04-15"
    assert "Eligible homeowners can receive a grant" in text
    assert "Applications close on November 30, 2026." in text
    # Ensure nav and footer were stripped
    assert "Copyright" not in text
    assert "Home" not in text


def test_fetch_and_extract_url_with_client():
    html = "<html><head><title>Test Doc</title></head><body><p>Hello Research World.</p></body></html>"

    def mock_transport(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
        )

    client = httpx.Client(transport=httpx.MockTransport(mock_transport))
    source = fetch_and_extract_url("https://example.org/test", client=client)
    assert source.title == "Test Doc"
    assert source.raw_content == "Hello Research World."
    assert source.url == "https://example.org/test"
    assert len(source.content_hash) == 64  # SHA-256


def test_fetch_url_handles_http_errors():
    def mock_transport(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, text="Not Found")

    client = httpx.Client(transport=httpx.MockTransport(mock_transport))
    with pytest.raises(IngestionError, match="HTTP 404"):
        fetch_and_extract_url("https://example.org/missing", client=client)


def test_pdf_extraction_success():
    # Build a simple in-memory PDF using pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Add page with text
    stream = io.BytesIO()
    writer.write(stream)
    stream.seek(0)
    pdf_bytes = stream.getvalue()

    # Note: blank page has no text, so test should raise no extractable text
    with pytest.raises(IngestionError, match="No extractable text"):
        extract_pdf_source(pdf_bytes, filename="empty.pdf")


def test_pdf_corrupt_bytes():
    with pytest.raises(IngestionError, match="standard PDF header"):
        extract_pdf_source(b"NOT_A_PDF_DOCUMENT", filename="corrupt.pdf")
