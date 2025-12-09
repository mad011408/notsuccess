"""NEXUS AI Agent - Statistics Tool"""

import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DescriptiveStats:
    """Descriptive statistics"""
    count: int = 0
    mean: float = 0.0
    median: float = 0.0
    mode: Optional[float] = None
    std: float = 0.0
    variance: float = 0.0
    min: float = 0.0
    max: float = 0.0
    range: float = 0.0
    q1: float = 0.0
    q3: float = 0.0
    iqr: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0


class StatisticsTool:
    """Statistical calculations"""

    def descriptive_stats(self, data: List[float]) -> DescriptiveStats:
        """
        Calculate descriptive statistics

        Args:
            data: List of numeric values

        Returns:
            DescriptiveStats object
        """
        if not data:
            return DescriptiveStats()

        n = len(data)
        sorted_data = sorted(data)

        stats = DescriptiveStats(count=n)

        # Mean
        stats.mean = sum(data) / n

        # Median
        mid = n // 2
        if n % 2 == 0:
            stats.median = (sorted_data[mid - 1] + sorted_data[mid]) / 2
        else:
            stats.median = sorted_data[mid]

        # Mode
        from collections import Counter
        counts = Counter(data)
        max_count = max(counts.values())
        modes = [k for k, v in counts.items() if v == max_count]
        stats.mode = modes[0] if len(modes) == 1 else None

        # Variance and Standard Deviation
        stats.variance = sum((x - stats.mean) ** 2 for x in data) / n
        stats.std = math.sqrt(stats.variance)

        # Min, Max, Range
        stats.min = min(data)
        stats.max = max(data)
        stats.range = stats.max - stats.min

        # Quartiles
        stats.q1 = self._percentile(sorted_data, 25)
        stats.q3 = self._percentile(sorted_data, 75)
        stats.iqr = stats.q3 - stats.q1

        # Skewness
        if stats.std > 0:
            stats.skewness = sum((x - stats.mean) ** 3 for x in data) / (n * stats.std ** 3)

        # Kurtosis
        if stats.std > 0:
            stats.kurtosis = sum((x - stats.mean) ** 4 for x in data) / (n * stats.std ** 4) - 3

        return stats

    def _percentile(self, sorted_data: List[float], p: float) -> float:
        """Calculate percentile"""
        n = len(sorted_data)
        k = (n - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return sorted_data[int(k)]

        return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)

    def correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient

        Args:
            x: First variable
            y: Second variable

        Returns:
            Correlation coefficient
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if denom_x * denom_y == 0:
            return 0.0

        return numerator / (denom_x * denom_y)

    def covariance(self, x: List[float], y: List[float]) -> float:
        """Calculate covariance"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        return sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n

    def linear_regression(
        self,
        x: List[float],
        y: List[float]
    ) -> Dict[str, float]:
        """
        Simple linear regression

        Args:
            x: Independent variable
            y: Dependent variable

        Returns:
            Dict with slope, intercept, r_squared
        """
        if len(x) != len(y) or len(x) < 2:
            return {"slope": 0, "intercept": 0, "r_squared": 0}

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Calculate slope
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        if denominator == 0:
            return {"slope": 0, "intercept": mean_y, "r_squared": 0}

        slope = numerator / denominator
        intercept = mean_y - slope * mean_x

        # R-squared
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared
        }

    def t_test(
        self,
        sample1: List[float],
        sample2: Optional[List[float]] = None,
        mu: float = 0
    ) -> Dict[str, float]:
        """
        Perform t-test

        Args:
            sample1: First sample
            sample2: Second sample (for two-sample test)
            mu: Population mean (for one-sample test)

        Returns:
            Dict with t_statistic, degrees of freedom
        """
        if not sample1:
            return {"t_statistic": 0, "df": 0}

        n1 = len(sample1)
        mean1 = sum(sample1) / n1
        var1 = sum((x - mean1) ** 2 for x in sample1) / (n1 - 1)

        if sample2:
            # Two-sample t-test
            n2 = len(sample2)
            mean2 = sum(sample2) / n2
            var2 = sum((x - mean2) ** 2 for x in sample2) / (n2 - 1)

            pooled_se = math.sqrt(var1 / n1 + var2 / n2)
            if pooled_se == 0:
                return {"t_statistic": 0, "df": n1 + n2 - 2}

            t_stat = (mean1 - mean2) / pooled_se
            df = n1 + n2 - 2

        else:
            # One-sample t-test
            se = math.sqrt(var1 / n1)
            if se == 0:
                return {"t_statistic": 0, "df": n1 - 1}

            t_stat = (mean1 - mu) / se
            df = n1 - 1

        return {"t_statistic": t_stat, "df": df}

    def chi_square(
        self,
        observed: List[float],
        expected: List[float]
    ) -> Dict[str, float]:
        """
        Chi-square test

        Args:
            observed: Observed frequencies
            expected: Expected frequencies

        Returns:
            Chi-square statistic and degrees of freedom
        """
        if len(observed) != len(expected):
            return {"chi_square": 0, "df": 0}

        chi_sq = sum(
            (o - e) ** 2 / e
            for o, e in zip(observed, expected)
            if e > 0
        )

        return {
            "chi_square": chi_sq,
            "df": len(observed) - 1
        }

    def z_score(self, value: float, mean: float, std: float) -> float:
        """Calculate z-score"""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def normalize(self, data: List[float]) -> List[float]:
        """Min-max normalization"""
        if not data:
            return []

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            return [0.0] * len(data)

        return [(x - min_val) / range_val for x in data]

    def standardize(self, data: List[float]) -> List[float]:
        """Z-score standardization"""
        if not data:
            return []

        mean = sum(data) / len(data)
        std = math.sqrt(sum((x - mean) ** 2 for x in data) / len(data))

        if std == 0:
            return [0.0] * len(data)

        return [(x - mean) / std for x in data]

    def moving_average(
        self,
        data: List[float],
        window: int = 3
    ) -> List[float]:
        """Calculate moving average"""
        if len(data) < window:
            return data.copy()

        result = []
        for i in range(len(data) - window + 1):
            avg = sum(data[i:i + window]) / window
            result.append(avg)

        return result

    def exponential_smoothing(
        self,
        data: List[float],
        alpha: float = 0.3
    ) -> List[float]:
        """Exponential smoothing"""
        if not data:
            return []

        result = [data[0]]
        for i in range(1, len(data)):
            smoothed = alpha * data[i] + (1 - alpha) * result[-1]
            result.append(smoothed)

        return result

