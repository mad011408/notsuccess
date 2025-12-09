"""NEXUS AI Agent - Markdown Tool"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MarkdownHeading:
    """Markdown heading"""
    level: int
    text: str
    line_number: int


@dataclass
class MarkdownLink:
    """Markdown link"""
    text: str
    url: str
    is_image: bool = False


@dataclass
class MarkdownCodeBlock:
    """Markdown code block"""
    language: str
    code: str
    line_number: int


@dataclass
class MarkdownDocument:
    """Parsed markdown document"""
    content: str
    headings: List[MarkdownHeading] = field(default_factory=list)
    links: List[MarkdownLink] = field(default_factory=list)
    code_blocks: List[MarkdownCodeBlock] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)


class MarkdownTool:
    """Parse and generate Markdown"""

    def parse(self, content: str) -> MarkdownDocument:
        """
        Parse markdown content

        Args:
            content: Markdown string

        Returns:
            MarkdownDocument object
        """
        doc = MarkdownDocument(content=content)
        lines = content.split('\n')

        # Parse headings
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        for i, line in enumerate(lines):
            match = heading_pattern.match(line)
            if match:
                doc.headings.append(MarkdownHeading(
                    level=len(match.group(1)),
                    text=match.group(2),
                    line_number=i + 1
                ))

        # Parse links
        link_pattern = re.compile(r'(!?)\[([^\]]*)\]\(([^)]+)\)')
        for match in link_pattern.finditer(content):
            doc.links.append(MarkdownLink(
                text=match.group(2),
                url=match.group(3),
                is_image=bool(match.group(1))
            ))

        # Parse code blocks
        code_pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
        for match in code_pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            doc.code_blocks.append(MarkdownCodeBlock(
                language=match.group(1) or 'text',
                code=match.group(2).strip(),
                line_number=line_num
            ))

        # Parse tables
        doc.tables = self._parse_tables(content)

        return doc

    def _parse_tables(self, content: str) -> List[List[List[str]]]:
        """Parse markdown tables"""
        tables = []
        lines = content.split('\n')
        current_table = []
        in_table = False

        for line in lines:
            if '|' in line and not line.strip().startswith('```'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if cells and not all(set(c) <= {'-', ':'} for c in cells):
                    current_table.append(cells)
                    in_table = True
            elif in_table:
                if current_table:
                    tables.append(current_table)
                current_table = []
                in_table = False

        if current_table:
            tables.append(current_table)

        return tables

    def read_file(self, path: str) -> MarkdownDocument:
        """Read and parse markdown file"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse(content)

    def to_html(self, content: str) -> str:
        """Convert markdown to HTML"""
        try:
            import markdown
            return markdown.markdown(content, extensions=['tables', 'fenced_code'])
        except ImportError:
            # Basic conversion
            html = content

            # Headers
            for i in range(6, 0, -1):
                pattern = re.compile(f'^{"#" * i}\\s+(.+)$', re.MULTILINE)
                html = pattern.sub(f'<h{i}>\\1</h{i}>', html)

            # Bold
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

            # Italic
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

            # Links
            html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

            # Images
            html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', html)

            # Paragraphs
            html = '<p>' + '</p><p>'.join(html.split('\n\n')) + '</p>'

            return html

    def to_plain_text(self, content: str) -> str:
        """Convert markdown to plain text"""
        text = content

        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)

        # Remove headers markers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        # Remove emphasis
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)

        # Convert links to text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

        return text.strip()

    def get_toc(self, content: str) -> str:
        """Generate table of contents"""
        doc = self.parse(content)
        toc_lines = []

        for heading in doc.headings:
            indent = "  " * (heading.level - 1)
            anchor = heading.text.lower().replace(' ', '-')
            anchor = re.sub(r'[^a-z0-9-]', '', anchor)
            toc_lines.append(f"{indent}- [{heading.text}](#{anchor})")

        return '\n'.join(toc_lines)

    def create_heading(self, text: str, level: int = 1) -> str:
        """Create markdown heading"""
        return f"{'#' * level} {text}"

    def create_link(self, text: str, url: str) -> str:
        """Create markdown link"""
        return f"[{text}]({url})"

    def create_image(self, alt: str, url: str) -> str:
        """Create markdown image"""
        return f"![{alt}]({url})"

    def create_code_block(self, code: str, language: str = "") -> str:
        """Create markdown code block"""
        return f"```{language}\n{code}\n```"

    def create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """Create markdown table"""
        lines = []

        # Header
        lines.append("| " + " | ".join(headers) + " |")

        # Separator
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Rows
        for row in rows:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")

        return '\n'.join(lines)

    def create_list(self, items: List[str], ordered: bool = False) -> str:
        """Create markdown list"""
        lines = []
        for i, item in enumerate(items):
            prefix = f"{i + 1}." if ordered else "-"
            lines.append(f"{prefix} {item}")
        return '\n'.join(lines)

