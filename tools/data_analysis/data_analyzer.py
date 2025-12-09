"""NEXUS AI Agent - Data Analyzer"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class DataSummary:
    """Data summary statistics"""
    row_count: int = 0
    column_count: int = 0
    columns: List[str] = field(default_factory=list)
    dtypes: Dict[str, str] = field(default_factory=dict)
    missing_values: Dict[str, int] = field(default_factory=dict)
    numeric_summary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    categorical_summary: Dict[str, Dict[str, int]] = field(default_factory=dict)


class DataAnalyzer:
    """Analyze data structures"""

    def __init__(self):
        self._df = None

    def load_csv(self, path: str, **kwargs) -> bool:
        """Load CSV file"""
        try:
            import pandas as pd
            self._df = pd.read_csv(path, **kwargs)
            return True
        except Exception:
            return False

    def load_json(self, path: str, **kwargs) -> bool:
        """Load JSON file"""
        try:
            import pandas as pd
            self._df = pd.read_json(path, **kwargs)
            return True
        except Exception:
            return False

    def load_excel(self, path: str, **kwargs) -> bool:
        """Load Excel file"""
        try:
            import pandas as pd
            self._df = pd.read_excel(path, **kwargs)
            return True
        except Exception:
            return False

    def load_dataframe(self, df) -> None:
        """Load pandas DataFrame"""
        self._df = df

    def get_summary(self) -> DataSummary:
        """Get data summary"""
        if self._df is None:
            return DataSummary()

        summary = DataSummary(
            row_count=len(self._df),
            column_count=len(self._df.columns),
            columns=list(self._df.columns)
        )

        # Data types
        summary.dtypes = {col: str(dtype) for col, dtype in self._df.dtypes.items()}

        # Missing values
        summary.missing_values = self._df.isnull().sum().to_dict()

        # Numeric summary
        numeric_cols = self._df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            summary.numeric_summary[col] = {
                'mean': float(self._df[col].mean()),
                'std': float(self._df[col].std()),
                'min': float(self._df[col].min()),
                'max': float(self._df[col].max()),
                'median': float(self._df[col].median()),
            }

        # Categorical summary
        cat_cols = self._df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            value_counts = self._df[col].value_counts().head(10).to_dict()
            summary.categorical_summary[col] = {str(k): v for k, v in value_counts.items()}

        return summary

    def describe(self) -> Dict[str, Any]:
        """Get pandas describe output"""
        if self._df is None:
            return {}
        return self._df.describe().to_dict()

    def get_correlations(self) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix"""
        if self._df is None:
            return {}

        numeric_df = self._df.select_dtypes(include=['number'])
        if numeric_df.empty:
            return {}

        return numeric_df.corr().to_dict()

    def get_value_counts(self, column: str, top_n: int = 10) -> Dict[str, int]:
        """Get value counts for column"""
        if self._df is None or column not in self._df.columns:
            return {}
        return self._df[column].value_counts().head(top_n).to_dict()

    def filter_data(
        self,
        column: str,
        operator: str,
        value: Any
    ) -> int:
        """
        Filter data

        Args:
            column: Column name
            operator: Comparison operator
            value: Value to compare

        Returns:
            Number of rows after filter
        """
        if self._df is None or column not in self._df.columns:
            return 0

        ops = {
            '==': lambda x, v: x == v,
            '!=': lambda x, v: x != v,
            '>': lambda x, v: x > v,
            '>=': lambda x, v: x >= v,
            '<': lambda x, v: x < v,
            '<=': lambda x, v: x <= v,
            'contains': lambda x, v: x.str.contains(v, na=False),
            'startswith': lambda x, v: x.str.startswith(v, na=False),
            'endswith': lambda x, v: x.str.endswith(v, na=False),
        }

        if operator in ops:
            self._df = self._df[ops[operator](self._df[column], value)]

        return len(self._df)

    def group_by(
        self,
        columns: List[str],
        agg_column: str,
        agg_func: str = 'mean'
    ) -> Dict[str, Any]:
        """Group and aggregate data"""
        if self._df is None:
            return {}

        try:
            grouped = self._df.groupby(columns)[agg_column].agg(agg_func)
            return grouped.to_dict()
        except Exception:
            return {}

    def pivot_table(
        self,
        values: str,
        index: str,
        columns: str,
        aggfunc: str = 'mean'
    ) -> Dict[str, Any]:
        """Create pivot table"""
        if self._df is None:
            return {}

        try:
            import pandas as pd
            pivot = pd.pivot_table(
                self._df,
                values=values,
                index=index,
                columns=columns,
                aggfunc=aggfunc
            )
            return pivot.to_dict()
        except Exception:
            return {}

    def detect_outliers(
        self,
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> List[int]:
        """
        Detect outliers

        Args:
            column: Column to check
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold value

        Returns:
            List of outlier indices
        """
        if self._df is None or column not in self._df.columns:
            return []

        data = self._df[column].dropna()

        if method == 'iqr':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = self._df[
                (self._df[column] < Q1 - threshold * IQR) |
                (self._df[column] > Q3 + threshold * IQR)
            ].index.tolist()

        elif method == 'zscore':
            mean = data.mean()
            std = data.std()
            z_scores = abs((self._df[column] - mean) / std)
            outliers = self._df[z_scores > threshold].index.tolist()

        else:
            outliers = []

        return outliers

    def get_missing_info(self) -> Dict[str, Any]:
        """Get missing value information"""
        if self._df is None:
            return {}

        missing = self._df.isnull().sum()
        total = len(self._df)

        return {
            col: {
                'count': int(count),
                'percentage': round(count / total * 100, 2)
            }
            for col, count in missing.items() if count > 0
        }

    def to_dict(self, orient: str = 'records') -> Union[List, Dict]:
        """Convert to dictionary"""
        if self._df is None:
            return []
        return self._df.to_dict(orient=orient)

    def head(self, n: int = 5) -> List[Dict]:
        """Get first n rows"""
        if self._df is None:
            return []
        return self._df.head(n).to_dict('records')

    def tail(self, n: int = 5) -> List[Dict]:
        """Get last n rows"""
        if self._df is None:
            return []
        return self._df.tail(n).to_dict('records')

