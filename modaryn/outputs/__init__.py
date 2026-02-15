from abc import ABC, abstractmethod
from typing import Optional, List # Added List
from modaryn.domain.model import DbtProject, DbtModel # Added DbtModel

class OutputGenerator(ABC):
    @abstractmethod
    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False) -> Optional[str]:
        """
        Generates a combined scan and score report for the given DbtProject.
        Returns a string for file-based formats, or None if printing directly to console.
        """
        pass
