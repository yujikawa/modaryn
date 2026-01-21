from modaryn.domain.model import DbtProject


def markdown_output(project: DbtProject) -> str:
    """
    Generates a Markdown report from a DbtProject.
    """
    lines = [
        "# Modaryn Scan Report",
        "",
        "| Model Name | JOINs | CTEs | Downstream Children |",
        "|------------|-------|------|---------------------|",
    ]

    sorted_models = sorted(
        project.models.values(),
        key=lambda m: m.downstream_model_count,
        reverse=True,
    )

    for model in sorted_models:
        if model.complexity:
            join_count = str(model.complexity.join_count)
            cte_count = str(model.complexity.cte_count)
        else:
            join_count = "N/A"
            cte_count = "N/A"

        lines.append(
            f"| {model.model_name} | {join_count} | {cte_count} | {model.downstream_model_count} |"
        )

    return "\n".join(lines)
