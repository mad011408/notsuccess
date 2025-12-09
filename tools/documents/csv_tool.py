"""NEXUS AI Agent - CSV Tool"""

import csv
import io
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class CSVData:
    """CSV data"""
    path: str
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    error: Optional[str] = None


class CSVTool:
    """Read and write CSV files"""

    def read(
        self,
        path: str,
        delimiter: str = ',',
        has_header: bool = True,
        encoding: str = 'utf-8',
        limit: Optional[int] = None
    ) -> CSVData:
        """
        Read CSV file

        Args:
            path: CSV file path
            delimiter: Field delimiter
            has_header: First row is header
            encoding: File encoding
            limit: Maximum rows to read

        Returns:
            CSVData object
        """
        try:
            data = CSVData(path=path)

            with open(path, 'r', encoding=encoding, newline='') as f:
                reader = csv.reader(f, delimiter=delimiter)

                if has_header:
                    data.headers = next(reader, [])

                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    data.rows.append(row)

            data.row_count = len(data.rows)
            data.column_count = len(data.headers) if data.headers else (
                len(data.rows[0]) if data.rows else 0
            )

            return data

        except Exception as e:
            return CSVData(path=path, error=str(e))

    def read_as_dicts(
        self,
        path: str,
        delimiter: str = ',',
        encoding: str = 'utf-8',
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Read CSV as list of dictionaries"""
        try:
            with open(path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = []
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    rows.append(dict(row))
                return rows
        except Exception:
            return []

    def write(
        self,
        path: str,
        data: List[List[str]],
        headers: Optional[List[str]] = None,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> bool:
        """
        Write CSV file

        Args:
            path: Output path
            data: Row data
            headers: Column headers
            delimiter: Field delimiter
            encoding: File encoding

        Returns:
            Success status
        """
        try:
            with open(path, 'w', encoding=encoding, newline='') as f:
                writer = csv.writer(f, delimiter=delimiter)
                if headers:
                    writer.writerow(headers)
                writer.writerows(data)
            return True
        except Exception:
            return False

    def write_dicts(
        self,
        path: str,
        data: List[Dict[str, Any]],
        fieldnames: Optional[List[str]] = None,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> bool:
        """Write list of dictionaries to CSV"""
        if not data:
            return False

        try:
            fieldnames = fieldnames or list(data[0].keys())

            with open(path, 'w', encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception:
            return False

    def to_string(
        self,
        data: List[List[str]],
        headers: Optional[List[str]] = None,
        delimiter: str = ','
    ) -> str:
        """Convert data to CSV string"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)
        return output.getvalue()

    def from_string(
        self,
        csv_string: str,
        delimiter: str = ',',
        has_header: bool = True
    ) -> CSVData:
        """Parse CSV from string"""
        data = CSVData(path="<string>")

        try:
            reader = csv.reader(io.StringIO(csv_string), delimiter=delimiter)

            if has_header:
                data.headers = next(reader, [])

            data.rows = list(reader)
            data.row_count = len(data.rows)
            data.column_count = len(data.headers) if data.headers else (
                len(data.rows[0]) if data.rows else 0
            )

        except Exception as e:
            data.error = str(e)

        return data

    def get_column(self, path: str, column: int, has_header: bool = True) -> List[str]:
        """Get specific column"""
        data = self.read(path, has_header=has_header)
        if data.error:
            return []
        return [row[column] for row in data.rows if len(row) > column]

    def filter_rows(
        self,
        path: str,
        column: int,
        value: str,
        has_header: bool = True
    ) -> List[List[str]]:
        """Filter rows by column value"""
        data = self.read(path, has_header=has_header)
        if data.error:
            return []
        return [row for row in data.rows if len(row) > column and row[column] == value]

    def get_stats(self, path: str) -> Dict[str, Any]:
        """Get CSV statistics"""
        data = self.read(path)
        if data.error:
            return {"error": data.error}

        return {
            "rows": data.row_count,
            "columns": data.column_count,
            "headers": data.headers,
            "sample": data.rows[:5] if data.rows else []
        }

