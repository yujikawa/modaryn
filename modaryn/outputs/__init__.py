from abc import ABC, abstractmethod
from typing import Optional

from modaryn.domain.model import DbtProject


class OutputGenerator(ABC):
    @abstractmethod
    def generate_scan_report(self, project: DbtProject) -> Optional[str]:
        """
        Generates a scan report for the given DbtProject.
        Returns a string for file-based formats, or None if printing directly to console.
        """
        pass

    @abstractmethod
    def generate_score_report(self, project: DbtProject) -> Optional[str]:
        """
        Generates a score report for the given DbtProject.
        Returns a string for file-based formats, or None if printing directly to console.
        """
        pass
