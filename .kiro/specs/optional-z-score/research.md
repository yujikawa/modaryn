# Research & Design Decisions Template

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.

**Usage**:
- Log research activities and outcomes during the discovery phase.
- Document design decision trade-offs that are too detailed for `design.md`.
- Provide references and evidence for future audits or reuse.
---

## Summary
- **Feature**: `optional-z-score`
- **Discovery Scope**: Extension
- **Key Findings**:
  - The `Scorer.score_project` method currently calculates and assigns z-scores to `model.score` by default, without retaining raw scores.
  - CLI argument parsing is handled by `typer`, allowing for easy addition of new options.
  - Output generators consume `model.score` directly, meaning changes to scoring logic will impact output presentation.

## Research Log
Document notable investigation steps and their outcomes. Group entries by topic for readability.

### Current Scoring Mechanism in `modaryn/scorers/score.py`
- **Context**: Understand how `modaryn` currently calculates and assigns scores to dbt models.
- **Sources Consulted**: `modaryn/scorers/score.py`
- **Findings**:
    - `Scorer._calculate_raw_score` computes a raw score based on `complexity` and `importance` weights.
    - `Scorer.score_project` iterates through models, calculates raw scores, then computes mean and standard deviation of these raw scores.
    - Subsequently, `model.score` is *overwritten* with the z-score: `model.score = (raw_score - mean_score) / std_dev`.
    - This means `model.score` *always* holds the z-score after `score_project` is called. Raw scores are not stored persistently on the `DbtModel` object.
- **Implications**: To make z-score optional and raw score the default, `DbtModel` needs to store both raw and z-scores, and `score_project` needs to conditionally apply z-score.

### CLI Argument Handling in `modaryn/cli.py`
- **Context**: Identify how new command-line options can be added to control the z-score feature.
- **Sources Consulted**: `modaryn/cli.py`
- **Findings**:
    - The `typer` library is used for CLI argument parsing.
    - Options are defined using `typer.Option(...)`.
    - The `score` command takes various options like `--project-path`, `--dialect`, `--config`, `--format`, `--output`.
- **Implications**: A new `typer.Option` can be introduced to `modaryn.cli.score` to control the z-score behavior, and its value passed down to the `Scorer` class.

### Score Output and Presentation
- **Context**: Understand how scores are currently displayed to users.
- **Sources Consulted**: `modaryn/cli.py` (how `OutputGenerator` is used), `modaryn/outputs/terminal.py`, `modaryn/outputs/markdown.py`
- **Findings**:
    - After scoring, an `OutputGenerator` (e.g., `TerminalOutput`, `MarkdownOutput`, `HtmlOutput`) is instantiated and its `generate_report` method is called with the `project` object.
    - These generators access `model.score` directly.
    - No explicit indication of whether z-score has been applied is currently presented in the output.
- **Implications**: Output generators need to be updated to:
    1. Decide which score (`raw_score` or `z_score`) to display based on the CLI option.
    2. Clearly indicate if the displayed scores are z-scores or raw scores.

## Architecture Pattern Evaluation
- **Option**: Extend existing `Scorer` and `DbtModel`
- **Description**: Modify the `Scorer` class to compute and store both raw and z-scores, and update `DbtModel` to hold these. Introduce a CLI flag to control which score is presented.
- **Strengths**: Minimal impact on overall architecture, leverages existing components.
- **Risks / Limitations**: Requires careful modification of a central data model (`DbtModel`) and scoring logic.
- **Notes**: Aligns with existing `modaryn` monolithic architecture.

## Design Decisions

### Decision: Introduce separate score fields in `DbtModel`
- **Context**: The current `DbtModel.score` field is overwritten with the z-score, discarding the raw score. To support optional z-scoring, both values are needed.
- **Alternatives Considered**:
  1. Store only `raw_score` in `DbtModel` and calculate `z_score` dynamically in output. (Rejected due to potential performance overhead for repeated calculations and complexity of passing `mean_score` and `std_dev` around).
  2. Overload `DbtModel.score` based on a flag. (Rejected for ambiguity and potential for errors).
- **Selected Approach**: Add `raw_score: float` and rename existing `score` to `z_score: float` (or add `z_score` and keep `score` for raw). Let's go with adding `raw_score` and `z_score` to `DbtModel`. The existing `score` attribute would then be deprecated or removed.
- **Rationale**: Provides clear separation of concerns, easy access to both values, and maintains type safety.

### Decision: Control z-score application via CLI flag
- **Context**: Users need a clear way to specify if they want z-score transformed scores or raw scores.
- **Alternatives Considered**:
  1. Configuration file setting. (Rejected for less immediate user control and potential for overriding other settings).
  2. Separate `zscore` command. (Rejected for unnecessary command proliferation).
- **Selected Approach**: Add a `typer.Option` to the `score` command, e.g., `--apply-zscore` (defaulting to `False`).
- **Rationale**: Simple, direct user control, consistent with existing CLI patterns.

## Risks & Mitigations
- **Risk**: Modifying `DbtModel` might impact other parts of the system that rely on `model.score`.
  - **Proposed mitigation**: Perform a thorough codebase search for all usages of `DbtModel.score` to ensure compatibility or update dependent components.
- **Risk**: Output generators might not correctly interpret or display the new score fields or z-score application status.
  - **Proposed mitigation**: Clearly define new interfaces/parameters for output generators to pass `apply_zscore` status and access specific score fields.

## References
- `modaryn/scorers/score.py` — Current scoring implementation.
- `modaryn/cli.py` — CLI command and option definitions.
- `modaryn/domain/model.py` — Definition of `DbtModel`.
