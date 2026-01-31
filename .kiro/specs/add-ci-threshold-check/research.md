# Research Log: add-ci-threshold-check

## Summary
This feature introduces a new CI-specific command to `modaryn` that checks dbt model scores against a defined threshold. The command will leverage existing scoring mechanisms and output formats, with added logic to highlight problematic models and exit with an appropriate status code for CI pipelines.

## Research Topics

### 1. Existing CLI Command Structure
**Source**: `modaryn/cli.py` via `grep "typer." modaryn/cli.py`
**Findings**:
- `modaryn` uses `typer.Typer` for defining CLI commands and options.
- Commands are defined as functions decorated with `@app.command()`.
- `typer.Option` is used to define command-line arguments.
- `typer.Exit(code=1)` is used for exiting with an error status.
**Implications**: A new `modaryn ci-check` command can be easily integrated by adding a new function to `modaryn/cli.py`.

### 2. Model Scoring Mechanism
**Source**: `modaryn/scorers/score.py` via `read_file`
**Findings**:
- The `Scorer` class calculates raw scores for dbt models.
- The `score_project` method normalizes these raw scores into Z-scores (standard deviations from the mean).
- The user's request explicitly mentions "z-scoreの閾値設定".
**Implications**: The existing `Scorer` class can be directly reused to obtain the necessary Z-scores for threshold checking. No new scoring logic is required.

### 3. Output Generation and Reporting
**Source**: `modaryn/cli.py` via `grep "output" modaryn/cli.py` and `modaryn/outputs/` directory structure.
**Findings**:
- `modaryn/cli.py` dynamically instantiates `OutputGenerator` implementations (e.g., `TerminalOutput`, `MarkdownOutput`, `HtmlOutput`).
- `generate_report(project)` method is called on the selected output generator to produce the report content.
- The report can be written to a file or printed to the console.
**Implications**: The new `ci-check` command can reuse existing output generators. For CI, `TerminalOutput` is likely the primary format. The output logic needs to be enhanced to highlight models exceeding the threshold.

### 4. Thresholding and CI Integration
**Source**: User request, general CI practices.
**Findings**:
- The core requirement is to fail CI if any model's score exceeds a specified threshold.
- The output should clearly indicate which models caused the failure.
**Implications**: The `ci-check` command will need to:
    - Accept a configurable threshold value.
    - Compare calculated Z-scores against this threshold.
    - Print all scores regardless of pass/fail.
    - If any model exceeds the threshold, print details of those models and exit with a non-zero status code.

## Architecture Pattern Evaluation
- **Reuse Existing Components**: The current architecture allows for direct reuse of `Scorer` and `OutputGenerator` components. This aligns with the "Extension" feature classification.
- **CLI Extension**: The `typer` framework makes it straightforward to add a new command without modifying core application flow for existing commands.

## Design Decisions
- **New Command**: Introduce `modaryn ci-check` in `modaryn/cli.py`.
- **Threshold Argument**: Add a `--threshold` option (float) to `modaryn ci-check`.
- **Scoring Logic**: Delegate to `modaryn.scorers.score.Scorer`.
- **Result Evaluation**: Implement logic within the `ci-check` command to evaluate model Z-scores against the `--threshold`.
- **Output Enhancement**: Modify the output generation (potentially within a new or extended output class, or directly in the `cli.py` command) to highlight models that exceed the threshold.
- **CI Exit Status**: Exit with `0` on success (no models exceed threshold), `1` on failure (one or more models exceed threshold).

## Risks
- **Output Customization**: Modifying existing `OutputGenerator`s might impact other commands. A dedicated CI output formatter or a mechanism to conditionally add threshold information might be needed to avoid this.
- **Threshold Type Extension**: While currently focused on Z-score, designing for future extensibility (e.g., different threshold types) should be considered but not over-engineered at this stage.