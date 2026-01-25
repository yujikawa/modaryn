# Product Overview

`modaryn` is a Python-based Command Line Interface (CLI) tool designed to analyze dbt (data build tool) projects. Its primary purpose is to score the complexity and structural importance of dbt models, helping data teams identify high-risk and high-impact data models within their projects.

## Core Capabilities

- **dbt Project Analysis**: Scans dbt project structures and model files.
- **Complexity Scoring**: Calculates complexity scores for dbt models based on SQL analysis (e.g., JOINs, CTEs, conditional logic).
- **Importance Scoring**: Determines the structural importance of models based on their dependencies.
- **Combined Scoring**: Ranks models using a weighted combination of complexity and importance scores.
- **Reporting**: Generates reports in various formats (Terminal, Markdown, HTML) to visualize the analysis results.

## Target Use Cases

- **Model Refactoring**: Identifying complex and unwieldy models that are prime candidates for refactoring.
- **Risk Assessment**: Pinpointing critical and complex models that pose a high risk if they fail.
- **Impact Analysis**: Understanding the downstream impact of changes to specific models.
- **Code Review**: Providing objective metrics to aid in the review of new or modified dbt models.

## Value Proposition

`modaryn` provides data teams with a quantitative and objective framework for managing the health and quality of their dbt projects. By systematically identifying high-risk and high-impact models, it enables teams to focus their efforts on what matters most, reducing maintenance overhead and improving data reliability.

---
_Focus on patterns and purpose, not exhaustive feature lists_
