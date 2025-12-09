"""NEXUS AI Agent - PDF Reader"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PDFPage:
    """PDF page content"""
    page_number: int
    text: str
    tables: List[List[List[str]]] = field(default_factory=list)
    images: List[bytes] = field(default_factory=list)


@dataclass
class PDFDocument:
    """PDF document content"""
    path: str
    pages: List[PDFPage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_pages: int = 0
    error: Optional[str] = None


class PDFReader:
    """Read PDF documents"""

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check for required libraries"""
        pass  # Will raise on use if not available

    def read(
        self,
        path: str,
        pages: Optional[List[int]] = None,
        extract_tables: bool = False,
        extract_images: bool = False
    ) -> PDFDocument:
        """
        Read PDF document

        Args:
            path: PDF file path
            pages: Specific pages to read (1-indexed)
            extract_tables: Extract tables
            extract_images: Extract images

        Returns:
            PDFDocument object
        """
        try:
            import PyPDF2

            doc = PDFDocument(path=path)

            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                doc.total_pages = len(reader.pages)

                # Extract metadata
                if reader.metadata:
                    doc.metadata = {
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'subject': reader.metadata.get('/Subject', ''),
                        'creator': reader.metadata.get('/Creator', ''),
                    }

                # Extract pages
                page_nums = pages or range(1, doc.total_pages + 1)
                for page_num in page_nums:
                    if 1 <= page_num <= doc.total_pages:
                        page = reader.pages[page_num - 1]
                        text = page.extract_text() or ""

                        pdf_page = PDFPage(
                            page_number=page_num,
                            text=text
                        )
                        doc.pages.append(pdf_page)

            return doc

        except ImportError:
            return PDFDocument(
                path=path,
                error="PyPDF2 not installed. Run: pip install PyPDF2"
            )
        except Exception as e:
            return PDFDocument(path=path, error=str(e))

    def read_with_pdfplumber(
        self,
        path: str,
        pages: Optional[List[int]] = None
    ) -> PDFDocument:
        """Read PDF with pdfplumber for better table extraction"""
        try:
            import pdfplumber

            doc = PDFDocument(path=path)

            with pdfplumber.open(path) as pdf:
                doc.total_pages = len(pdf.pages)

                page_nums = pages or range(1, doc.total_pages + 1)
                for page_num in page_nums:
                    if 1 <= page_num <= doc.total_pages:
                        page = pdf.pages[page_num - 1]

                        pdf_page = PDFPage(
                            page_number=page_num,
                            text=page.extract_text() or "",
                            tables=page.extract_tables() or []
                        )
                        doc.pages.append(pdf_page)

            return doc

        except ImportError:
            return PDFDocument(
                path=path,
                error="pdfplumber not installed. Run: pip install pdfplumber"
            )
        except Exception as e:
            return PDFDocument(path=path, error=str(e))

    def get_text(self, path: str) -> str:
        """Get all text from PDF"""
        doc = self.read(path)
        if doc.error:
            return ""
        return "\n\n".join(page.text for page in doc.pages)

    def get_page_text(self, path: str, page_number: int) -> str:
        """Get text from specific page"""
        doc = self.read(path, pages=[page_number])
        if doc.error or not doc.pages:
            return ""
        return doc.pages[0].text

    def search(self, path: str, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text in PDF"""
        doc = self.read(path)
        if doc.error:
            return []

        results = []
        for page in doc.pages:
            text = page.text if case_sensitive else page.text.lower()
            search_query = query if case_sensitive else query.lower()

            if search_query in text:
                results.append({
                    "page": page.page_number,
                    "text": page.text[:500]  # First 500 chars
                })

        return results

    def get_metadata(self, path: str) -> Dict[str, Any]:
        """Get PDF metadata"""
        doc = self.read(path)
        return doc.metadata

    def count_pages(self, path: str) -> int:
        """Get page count"""
        try:
            import PyPDF2
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return len(reader.pages)
        except:
            return 0

