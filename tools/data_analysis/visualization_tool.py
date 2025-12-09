"""NEXUS AI Agent - Visualization Tool"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ChartConfig:
    """Chart configuration"""
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    figsize: Tuple[int, int] = (10, 6)
    style: str = "seaborn"
    color: Optional[str] = None
    alpha: float = 1.0
    grid: bool = True
    legend: bool = True


class VisualizationTool:
    """Create data visualizations"""

    def __init__(self):
        self._fig = None
        self._ax = None

    def _setup_plot(self, config: ChartConfig):
        """Setup matplotlib plot"""
        import matplotlib.pyplot as plt

        plt.style.use(config.style if config.style in plt.style.available else 'default')
        self._fig, self._ax = plt.subplots(figsize=config.figsize)

        if config.title:
            self._ax.set_title(config.title)
        if config.xlabel:
            self._ax.set_xlabel(config.xlabel)
        if config.ylabel:
            self._ax.set_ylabel(config.ylabel)
        if config.grid:
            self._ax.grid(True, alpha=0.3)

    def line_chart(
        self,
        x: List[Any],
        y: List[float],
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Create line chart

        Args:
            x: X values
            y: Y values
            config: Chart configuration
            save_path: Path to save chart

        Returns:
            Path to saved chart or None
        """
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        self._ax.plot(x, y, color=config.color, alpha=config.alpha)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def bar_chart(
        self,
        categories: List[str],
        values: List[float],
        config: Optional[ChartConfig] = None,
        horizontal: bool = False,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create bar chart"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        if horizontal:
            self._ax.barh(categories, values, color=config.color, alpha=config.alpha)
        else:
            self._ax.bar(categories, values, color=config.color, alpha=config.alpha)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def scatter_plot(
        self,
        x: List[float],
        y: List[float],
        config: Optional[ChartConfig] = None,
        size: Optional[List[float]] = None,
        color: Optional[List[Any]] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create scatter plot"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        scatter = self._ax.scatter(
            x, y,
            s=size,
            c=color or config.color,
            alpha=config.alpha
        )

        if color and config.legend:
            plt.colorbar(scatter)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def histogram(
        self,
        data: List[float],
        bins: int = 30,
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create histogram"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        self._ax.hist(data, bins=bins, color=config.color, alpha=config.alpha, edgecolor='black')

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def pie_chart(
        self,
        labels: List[str],
        values: List[float],
        config: Optional[ChartConfig] = None,
        explode: Optional[List[float]] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create pie chart"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._fig, self._ax = plt.subplots(figsize=config.figsize)

        if config.title:
            self._ax.set_title(config.title)

        self._ax.pie(
            values,
            labels=labels,
            explode=explode,
            autopct='%1.1f%%',
            shadow=True
        )

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def box_plot(
        self,
        data: List[List[float]],
        labels: Optional[List[str]] = None,
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create box plot"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        bp = self._ax.boxplot(data, labels=labels)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def heatmap(
        self,
        data: List[List[float]],
        row_labels: Optional[List[str]] = None,
        col_labels: Optional[List[str]] = None,
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create heatmap"""
        import matplotlib.pyplot as plt
        import numpy as np

        config = config or ChartConfig()
        self._fig, self._ax = plt.subplots(figsize=config.figsize)

        if config.title:
            self._ax.set_title(config.title)

        im = self._ax.imshow(data, cmap='coolwarm')
        plt.colorbar(im)

        if row_labels:
            self._ax.set_yticks(range(len(row_labels)))
            self._ax.set_yticklabels(row_labels)

        if col_labels:
            self._ax.set_xticks(range(len(col_labels)))
            self._ax.set_xticklabels(col_labels, rotation=45)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def multi_line_chart(
        self,
        x: List[Any],
        y_series: Dict[str, List[float]],
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create multi-line chart"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        self._setup_plot(config)

        for label, y in y_series.items():
            self._ax.plot(x, y, label=label, alpha=config.alpha)

        if config.legend:
            self._ax.legend()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def subplots(
        self,
        charts: List[Dict[str, Any]],
        rows: int,
        cols: int,
        config: Optional[ChartConfig] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create subplot grid"""
        import matplotlib.pyplot as plt

        config = config or ChartConfig()
        fig, axes = plt.subplots(rows, cols, figsize=config.figsize)

        if config.title:
            fig.suptitle(config.title)

        axes_flat = axes.flatten() if hasattr(axes, 'flatten') else [axes]

        for i, (ax, chart) in enumerate(zip(axes_flat, charts)):
            chart_type = chart.get('type', 'line')
            data = chart.get('data', {})
            title = chart.get('title', '')

            ax.set_title(title)

            if chart_type == 'line':
                ax.plot(data.get('x', []), data.get('y', []))
            elif chart_type == 'bar':
                ax.bar(data.get('x', []), data.get('y', []))
            elif chart_type == 'scatter':
                ax.scatter(data.get('x', []), data.get('y', []))
            elif chart_type == 'hist':
                ax.hist(data.get('values', []), bins=data.get('bins', 30))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return save_path

        plt.show()
        return None

    def save_current(self, path: str, dpi: int = 150) -> str:
        """Save current figure"""
        import matplotlib.pyplot as plt

        if self._fig:
            self._fig.savefig(path, dpi=dpi, bbox_inches='tight')
            plt.close(self._fig)

        return path

