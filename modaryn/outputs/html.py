from jinja2 import Environment, FileSystemLoader
from typing import Optional, List

from modaryn.domain.model import DbtProject, DbtModel, ScoreStatistics
from . import OutputGenerator

HTML_SCORE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Modaryn Score and Scan Report</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; margin-top: 2em; }
        th, td { border: 1px solid #ccc; padding: 8px; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Modaryn Score and Scan Report</h1>
    
    <h2>Model Scores</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Model Name</th>
            <th>{% if apply_zscore %}Score (Z-Score){% else %}Score (Raw){% endif %}</th>
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
            <td>
                {% if apply_zscore %}
                    {{ "%.2f"|format(model.score) }}
                {% else %}
                    {{ "%.2f"|format(model.raw_score) }}
                {% endif %}
            </td>
            <td>{{ model.complexity.join_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.cte_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.conditional_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.where_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.sql_char_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.downstream_model_count }}</td>
        </tr>
        {% endfor %}
    </table>

    {% if statistics %}
    <h2>Score Statistics</h2>
    <ul>
        <li>Mean: {{ "%.3f"|format(statistics.mean) }}</li>
        <li>Median: {{ "%.3f"|format(statistics.median) }}</li>
        <li>Standard Deviation: {{ "%.3f"|format(statistics.std_dev) }}</li>
    </ul>
    {% endif %}

    {% if threshold is not none %}
    <h2>CI Check Summary</h2>
    <ul>
        <li>Status: {% if problematic_models %}<span style="color: red;">FAILED</span>{% else %}<span style="color: green;">PASSED</span>{% endif %} - 
            {% if problematic_models %}{{ problematic_models|length }} models exceeded threshold.{% else %}All models are within the defined threshold.{% endif %}</li>
        <li>Total models checked: {{ models|length }}</li>
        <li>Threshold: {{ "%.3f"|format(threshold) }}</li>
    </ul>
    {% endif %}

</body>
</html>
"""


class HtmlOutput(OutputGenerator):
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('.')) # Not used, but required

    def generate_report(self, project: DbtProject, problematic_models: Optional[List[DbtModel]] = None, threshold: Optional[float] = None, apply_zscore: bool = False, statistics: Optional[ScoreStatistics] = None) -> Optional[str]:
        sort_key = (lambda m: m.score) if apply_zscore else (lambda m: m.raw_score)
        
        sorted_models = sorted(
            project.models.values(), 
            key=lambda m: sort_key(m) if sort_key(m) is not None else -1,
            reverse=True
        )
        template = self.env.from_string(HTML_SCORE_TEMPLATE)
        return template.render(models=sorted_models, apply_zscore=apply_zscore, statistics=statistics, problematic_models=problematic_models, threshold=threshold)
