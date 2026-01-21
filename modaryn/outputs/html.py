from jinja2 import Environment, FileSystemLoader
from modaryn.domain.model import DbtProject

HTML_TEMPLATE = """
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
            <th>Score</th>
            <th>JOINs</th>
            <th>CTEs</th>
            <th>Downstream Models</th>
        </tr>
        {% for model in models %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ model.model_name }}</td>
            <td>{{ "%.2f"|format(model.score) }}</td>
            <td>{{ model.complexity.join_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.complexity.cte_count if model.complexity else 'N/A' }}</td>
            <td>{{ model.downstream_model_count }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


def html_output(project: DbtProject) -> str:
    """
    Generates a self-contained HTML report from a DbtProject.
    """
    sorted_models = sorted(
        project.models.values(), key=lambda m: m.score, reverse=True
    )

    # Render the Jinja2 template
    env = Environment(loader=FileSystemLoader('.')) # Not used, but required
    template = env.from_string(HTML_TEMPLATE)
    
    return template.render(models=sorted_models)
