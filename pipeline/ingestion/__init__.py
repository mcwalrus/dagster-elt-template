"""Ingestion layer — convert raw PDFs and DOCX files into structured markdown.

Writes raw output to ``data/sources/{pdf,docx}/``. Consumers MUST NOT
read from this directory — it is the ingestor's write-only scratch space.
"""

from pipeline.ingestion.docx_convert import convert_all_docx, convert_docx
from pipeline.ingestion.pdf_convert import convert_all_pdfs, convert_pdf

__all__ = ["convert_all_docx", "convert_all_pdfs", "convert_docx", "convert_pdf"]
