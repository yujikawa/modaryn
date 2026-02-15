# Implementation Plan

## Task Format Template

### Major + Sub-task structure
- [ ] 1. Refactor `DbtModel` for Dual Scoring (P)
- [x] 1.1 (P) Update `DbtModel` attributes
  - Add `raw_score: float = Field(default=0.0)`
  - Ensure `score: float` is explicitly used for z-score (or rename to `z_score` if appropriate after full codebase check). For now, `score` will hold the z-score.
  - _Requirements: 1.1, 2.1_

- [x] 2. Implement Conditional Z-score in Scorer (P)
- [x] 2.1 (P) Modify `Scorer.score_project` signature
  - Add `apply_zscore: bool = False` parameter.
  - _Requirements: 1.1, 2.1_
- [x] 2.2 (P) Implement raw score assignment
  - Inside `score_project`, assign calculated raw scores to `model.raw_score` for all models.
  - _Requirements: 2.1_
- [x] 2.3 (P) Implement conditional z-score calculation and assignment
  - If `apply_zscore` is `True`, calculate z-scores and assign them to `model.score`.
  - If `apply_zscore` is `False`, ensure `model.score` remains its default value (0.0).
  - _Requirements: 1.1, 2.1_

- [x] 3. Add CLI Option for Z-score Control (P)
- [x] 3.1 (P) Add `--apply-zscore` option to `cli.score` command
  - Define `apply_zscore: bool = typer.Option(False, "--apply-zscore", "-z", help="Apply Z-score transformation to model scores.")`
  - Set default value to `False`.
  - _Requirements: 1.2, 2.2_
- [x] 3.2 (P) Pass `apply_zscore` to `Scorer`
  - Pass the value of the new CLI option from `cli.score` command to `scorer.score_project()`.
  - _Requirements: 1.2_

- [ ] 4. Update Output Generators (P)
- [x] 4.1 (P) Update `OutputGenerator.generate_report` signature
  - Add `apply_zscore: bool = False` parameter.
  - _Requirements: 2.1, 3.1_
- [x] 4.2 (P) Modify `TerminalOutput` for score display and indicator
  - Adjust `TerminalOutput.generate_report` to show `model.raw_score` or `model.score` based on `apply_zscore`.
  - Add a visual indicator in the terminal report (e.g., a header line or column label) if z-scores are applied.
  - _Requirements: 2.1, 3.1_
- [x] 4.3 (P) Modify `MarkdownOutput` for score display and indicator
  - Adjust `MarkdownOutput.generate_report` to show `model.raw_score` or `model.score` based on `apply_zscore`.
  - Add a textual indicator (e.g., in a header or table caption) in the Markdown report if z-scores are applied.
  - _Requirements: 2.1, 3.1_
- [x] 4.4 (P) Modify `HtmlOutput` for score display and indicator
  - Adjust `HtmlOutput.generate_report` to show `model.raw_score` or `model.score` based on `apply_zscore`.
  - Add a textual or visual indicator (e.g., in a report title or table header) in the HTML report if z-scores are applied.
  - _Requirements: 2.1, 3.1_

- [ ] 5. Add Unit and Integration Tests (P)
- [ ] 5.1 (P) Add unit tests for `Scorer`
  - Test `score_project` with `apply_zscore=True` to verify `model.score` (z-score) population.
  - Test `score_project` with `apply_zscore=False` to verify `model.raw_score` population and `model.score` (z-score) is `0.0`.
  - _Requirements: 1.1, 2.1_
- [x] 5.2 (P) Add unit tests for `OutputGenerator` subclasses
  - Test `TerminalOutput.generate_report` for correct score display and z-score indicator based on `apply_zscore`.
  - Test `MarkdownOutput.generate_report` for correct score display and z-score indicator based on `apply_zscore`.
  - Test `HtmlOutput.generate_report` for correct score display and z-score indicator based on `apply_zscore`.
  - _Requirements: 2.1, 3.1_
- [x] 5.3 (P) Add integration tests for CLI
  - Test `modaryn score` command without `--apply-zscore` and verify raw scores are displayed and no z-score indicator.
  - Test `modaryn score --apply-zscore` command and verify z-scores are displayed and z-score indicator is present.
  - _Requirements: 1.2, 2.2, 3.1_
