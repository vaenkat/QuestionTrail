"""Safe PDF ingestion and page-level provenance extraction service."""

import io
from pypdf import PdfReader

from questiontrail.domain.models import (
    Source,
    SourceType,
    SourceAuthority,
    ExtractionStatus,
    utc_now,
)
from questiontrail.services.canonical import compute_content_hash
from questiontrail.services.url_ingestion import IngestionError

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


def extract_pdf_source(
    file_bytes: bytes,
    filename: str = "document.pdf",
    url: str | None = None,
) -> tuple[Source, dict[int, str]]:
    """Extract page-level text and metadata from PDF bytes.

    Returns:
        (Source, page_text_map: {page_number: text})
    Raises:
        IngestionError on invalid format, corrupt file, or size limit breach.
    """
    if not file_bytes:
        raise IngestionError("Uploaded PDF file is empty.")

    if len(file_bytes) > MAX_PDF_BYTES:
        raise IngestionError(f"PDF file size ({len(file_bytes)} bytes) exceeds 10MB limit.")

    # Validate header signature
    if not file_bytes.startswith(b"%PDF-"):
        raise IngestionError("Invalid file format. File does not start with standard PDF header '%PDF-'.")

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        raise IngestionError(f"Corrupted or unreadable PDF: {exc}") from exc

    num_pages = len(reader.pages)
    if num_pages == 0:
        raise IngestionError("PDF contains no readable pages.")

    page_map: dict[int, str] = {}
    combined_texts: list[str] = []

    for idx, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
            cleaned = "\n".join(line.strip() for line in page_text.splitlines() if line.strip())
            if cleaned:
                page_map[idx] = cleaned
                combined_texts.append(f"--- Page {idx} ---\n{cleaned}")
        except Exception:
            continue

    if not combined_texts:
        raise IngestionError("No extractable text found in PDF. The document may be scanned images without OCR.")

    full_text = "\n\n".join(combined_texts)
    content_hash = compute_content_hash(full_text)

    # Title extraction heuristic
    meta_title = ""
    try:
        if reader.metadata and reader.metadata.title:
            meta_title = str(reader.metadata.title).strip()
    except Exception:
        pass

    title = meta_title or filename or "Uploaded PDF Document"
    source_id = f"src-pdf-{content_hash[:8]}"

    source = Source(
        id=source_id,
        title=title,
        url=url,
        type=SourceType.pdf,
        authority=SourceAuthority.third_party,
        publication_date=None,
        cycle_or_version=None,
        retrieved_at=utc_now(),
        extraction_status=ExtractionStatus.success,
        content_hash=content_hash,
        raw_content=full_text,
        metadata={
            "filename": filename,
            "page_count": num_pages,
            "extracted_pages": len(page_map),
        },
    )

    return source, page_map
