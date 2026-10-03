"""Tests for storage provider and document extractor implementations."""

from __future__ import annotations

import io
import uuid
import pytest
from pypdf import PdfWriter
from docx import Document

from app.services.extractor import DocxExtractor, PdfExtractor, get_extractor
from app.services.storage import LocalStorageProvider


class TestDocumentExtractors:
    def test_pdf_extractor_success(self) -> None:
        """Create a real PDF in memory and extract text from it."""
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        # pypdf can write text or we can verify extraction works
        buf = io.BytesIO()
        writer.write(buf)
        pdf_bytes = buf.getvalue()

        extractor = PdfExtractor()
        text = extractor.extract(pdf_bytes)
        assert isinstance(text, str)

    def test_docx_extractor_success(self) -> None:
        """Create a real DOCX in memory and extract text from it."""
        doc = Document()
        doc.add_heading("Senior Backend Engineer", 0)
        doc.add_paragraph("Developed high-throughput distributed microservices with Python and FastAPI.")
        table = doc.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Skill"
        table.rows[0].cells[1].text = "Python"

        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()

        extractor = DocxExtractor()
        text = extractor.extract(docx_bytes)
        assert "Senior Backend Engineer" in text
        assert "Python and FastAPI" in text
        assert "Skill | Python" in text

    def test_get_extractor_factory(self) -> None:
        assert isinstance(get_extractor("resume.pdf"), PdfExtractor)
        assert isinstance(get_extractor("resume.PDF"), PdfExtractor)
        assert isinstance(get_extractor("application/pdf"), PdfExtractor)
        assert isinstance(get_extractor("resume.docx"), DocxExtractor)
        assert isinstance(get_extractor("resume.DOCX"), DocxExtractor)

        with pytest.raises(ValueError, match="Unsupported document format"):
            get_extractor("resume.txt")

        with pytest.raises(ValueError, match="Unsupported document format"):
            get_extractor("resume.exe")


class TestLocalStorageProvider:
    @pytest.mark.asyncio
    async def test_upload_and_download(self, tmp_path) -> None:
        storage = LocalStorageProvider(base_dir=tmp_path)
        user_id = uuid.uuid4()
        content = b"Candidate Resume Content"

        path = await storage.upload(content, "my_resume.pdf", user_id)
        assert await storage.exists(path) is True

        downloaded = await storage.download(path)
        assert downloaded == content

        deleted = await storage.delete(path)
        assert deleted is True
        assert await storage.exists(path) is False

    @pytest.mark.asyncio
    async def test_file_size_limit(self, tmp_path) -> None:
        storage = LocalStorageProvider(base_dir=tmp_path)
        user_id = uuid.uuid4()
        oversized = b"x" * (11 * 1024 * 1024)  # 11 MB > 10 MB limit

        with pytest.raises(ValueError, match="File size exceeds limit"):
            await storage.upload(oversized, "huge.pdf", user_id)

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, tmp_path) -> None:
        storage = LocalStorageProvider(base_dir=tmp_path)
        user_id = uuid.uuid4()
        content = b"Safe content"

        # Traversal in filename is sanitized to safe name
        path = await storage.upload(content, "../../etc/passwd.pdf", user_id)
        assert ".." not in path
        assert await storage.exists(path) is True

