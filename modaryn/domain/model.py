from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional


from modaryn.analyzers.sql_complexity import SqlComplexityResult


@dataclass
class ScoreStatistics:
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0


@dataclass
class ColumnReference:
    model_unique_id: str
    column_name: str


@dataclass
class DbtColumn:
    name: str
    description: str
    test_count: int = 0
    upstream_columns: List[ColumnReference] = field(default_factory=list)
    downstream_columns: List[ColumnReference] = field(default_factory=list)


@dataclass
class DbtModel:
    unique_id: str
    model_name: str
    file_path: Path
    raw_sql: str
    columns: Dict[str, "DbtColumn"] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    parents: Dict[str, "DbtModel"] = field(default_factory=dict)
    children: Dict[str, "DbtModel"] = field(default_factory=dict)
    complexity: Optional[SqlComplexityResult] = None
    raw_score: float = 0.0
    score: float = 0.0
    test_count: int = 0
    quality_score: float = 0.0

    @property
    def downstream_model_count(self) -> int:
        return len(self.children)

    @property
    def downstream_column_count(self) -> int:
        return sum(len(col.downstream_columns) for col in self.columns.values())

    @property
    def column_count(self) -> int:
        return len(self.columns)

    @property
    def tested_column_count(self) -> int:
        return len([col for col in self.columns.values() if col.test_count > 0])
    
    @property
    def column_test_coverage(self) -> float:
        if self.column_count == 0:
            return 0.0
        return (self.tested_column_count / self.column_count) * 100


@dataclass
class DbtProject:
    models: Dict[str, DbtModel] = field(default_factory=dict)
    statistics: Optional[ScoreStatistics] = None

    def __post_init__(self):
        self._build_dag()

    def _build_dag(self):
        for model in self.models.values():
            for dep_id in model.dependencies:
                if dep_id in self.models:
                    parent_model = self.models[dep_id]
                    model.parents[dep_id] = parent_model
                    parent_model.children[model.unique_id] = model

    def get_model(self, unique_id: str) -> DbtModel | None:
        return self.models.get(unique_id)
