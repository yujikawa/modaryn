from abc import ABC, abstractmethod
from typing import Optional

from modaryn.domain.model import DbtProject


class OutputGenerator(ABC):
    @abstractmethod
    def generate_report(self, project: DbtProject) -> Optional[str]:
        """
        Generates a combined scan and score report for the given DbtProject.
        Returns a string for file-based formats, or None if printing directly to console.
        """
        pass
