from jinja2 import Environment, FileSystemLoader
from typing import Optional

from modaryn.domain.model import DbtProject
from . import OutputGenerator

HTML_SCAN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Modaryn Scan Report</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; margin-top: 2em; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Modaryn Scan Report</h1>
    
    <h2>Model Details</h2>
    <table>
        <tr>
            <th>Model Name</th>
            <th>JOINs</th>
            <th>CTEs</th>
            <th>Conditionals</th>
            <th>WHEREs</th>
            <th>SQL Chars</th>
            <th>Downstream Models</th>
        </tr>
        {% for model in models %}
        <tr>
            <td>{{ model.model_name }}</td>
            <td>{{ model.complexity.join_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.cte_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.conditional_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.where_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.sql_char_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.downstream_model_count }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

HTML_SCORE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Modaryn Report</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; margin-top: 2em; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Modaryn Score Report</h1>
    
    <h2>Model Scores</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Model Name</th>
            <th>Score (Z-score)</th>
            <th>JOINs</th>
            <th>CTEs</th>
            <th>Conditionals</th>
            <th>WHEREs</th>
            <th>SQL Chars</th>
            <th>Downstream Models</th>
        </tr>
        {% for model in models %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ model.model_name }}</td>
            <td>{{ "%.2f"|format(model.score) }}</td>
            <td>{{ model.complexity.join_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.cte_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.conditional_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.where_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.sql_char_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.downstream_model_count }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


class HtmlOutput(OutputGenerator):
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('.')) # Not used, but required

    def generate_scan_report(self, project: DbtProject) -> Optional[str]:
        sorted_models = sorted(
            project.models.values(), key=lambda m: m.downstream_model_count, reverse=True
        )
        template = self.env.from_string(HTML_SCAN_TEMPLATE)
        return template.render(models=sorted_models)

    def generate_score_report(self, project: DbtProject) -> Optional[str]:
        sorted_models = sorted(
            project.models.values(), key=lambda m: m.score, reverse=True
        )
        template = self.env.from_string(HTML_SCORE_TEMPLATE)
        return template.render(models=sorted_models)
