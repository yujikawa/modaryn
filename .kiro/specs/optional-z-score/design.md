# Design Document Template

---
**Purpose**: Provide sufficient detail to ensure implementation consistency across different implementers, preventing interpretation drift.

**Approach**:
- Include essential sections that directly inform implementation decisions
- Omit optional sections unless critical to preventing implementation errors
- Match detail level to feature complexity
- Use diagrams and tables over lengthy prose

**Warning**: Approaching 1000 lines indicates excessive feature complexity that may require design simplification.
---

> Sections may be reordered (e.g., surfacing Requirements Traceability earlier or moving Data Models nearer Architecture) when it improves clarity. Within each section, keep the flow **Summary → Scope → Decisions → Impacts/Risks** so reviewers can scan consistently.

## Overview
This feature introduces an optional z-score transformation for `modaryn`'s model scoring. By default, raw scores will be displayed, and users can opt-in to view z-score transformed results via a CLI flag. This provides flexibility in score interpretation and aligns with standardized metric analysis.


### Goals
- Allow users to optionally apply z-score transformation to calculated scores.
- Make raw scores the default presentation, instead of z-scores.
- Clearly indicate if z-score transformation has been applied in the output.

### Non-Goals
- Changing the underlying raw score calculation logic.
- Introducing new scoring metrics beyond complexity and importance.
- Implementing persistent storage for scoring preferences.

## Architecture

> Reference detailed discovery notes in `research.md` only for background; keep design.md self-contained for reviewers by capturing all decisions and contracts here.
> Capture key decisions in text and let diagrams carry structural detail—avoid repeating the same information in prose.

### Existing Architecture Analysis (if applicable)
`modaryn` is a monolithic Python CLI application. The core flow involves `ManifestLoader` -> `Scorer` -> `OutputGenerator`. The `Scorer` currently calculates raw scores and then immediately overwrites `DbtModel.score` with the z-score.

### Architecture Pattern & Boundary Map
The existing architecture will be extended. The primary modifications will be within the `Scorer` and `DbtModel` components, with a new input option in the `cli.py` and adjustments to the `OutputGenerator` hierarchy.

### Technology Stack

| Layer             | Choice / Version | Role in Feature                                  | Notes                                                     |
| :---------------- | :--------------- | :----------------------------------------------- | :-------------------------------------------------------- |
| CLI               | Typer            | Argument parsing for z-score option              |                                                           |
| Backend / Services | Python 3.9+      | Core logic for score calculation and transformation | `numpy` for z-score calculation                           |
| Data / Storage    | In-memory Objects | `DbtModel` for storing scores                    | Extension to `DbtModel` to store both raw and z-scores. |

## System Flows

The primary system flow for scoring remains largely unchanged. The `CLI` receives user input, passes it to the `Scorer`, which processes `DbtProject` models and updates them. Finally, an `OutputGenerator` presents the results. The new `apply_zscore` flag will be passed from the `CLI` to the `Scorer` and then to the `OutputGenerator`.

## Requirements Traceability

Map each requirement ID (e.g., `2.1`) to the design elements that realize it.

| Requirement | Summary                                                              | Components                      | Interfaces                                                            | Flows |
| :---------- | :------------------------------------------------------------------- | :------------------------------ | :-------------------------------------------------------------------- | :---- |
| 1.1         | `modaryn` system shall apply z-score transformation to scores.       | `Scorer`, `DbtModel`            | `Scorer.score_project(apply_zscore: bool)`                            |       |
| 1.2         | `modaryn` system shall provide a mechanism to enable/disable z-score. | `CLI`                           | `cli.score` command with `--apply-zscore` option                      |       |
| 2.1         | `modaryn` system shall present scores without z-score (default).     | `Scorer`, `DbtModel`, `OutputGenerator` | `DbtModel.raw_score`, `OutputGenerator.generate_report(apply_zscore: bool)` |       |
| 2.2         | `modaryn` system shall default to z-score option disabled.           | `CLI`                           | `--apply-zscore` option default value                                 |       |
| 3.1         | `modaryn` system shall indicate if z-score applied.                  | `OutputGenerator`               | `OutputGenerator.generate_report(apply_zscore: bool)` for conditional output formatting |       |

## Components and Interfaces

### `modaryn/domain`

#### `DbtModel`

| Field      | Detail                                                                                                                  |
| :--------- | :---------------------------------------------------------------------------------------------------------------------- |
| Intent     | Data model representing a dbt model, extended to hold both raw and z-transformed scores for flexible reporting.         |
| Requirements | 1.1, 2.1                                                                                                                |

**Responsibilities & Constraints**
- Store `raw_score` after initial calculation.
- Store `z_score` if z-score transformation is applied.
- The existing `score` attribute will be re-purposed to explicitly hold the `z_score`.

**Contracts**: State

##### State Management
- State model:
  ```python
  class DbtModel:
      # ... existing attributes ...
      raw_score: float = Field(default=0.0) # New attribute to store the un-normalized score
      score: float = Field(default=0.0)     # Existing attribute, now explicitly for z-score
  ```

### `modaryn/scorers`

#### `Scorer`

| Field      | Detail                                                                           |
| :--------- | :------------------------------------------------------------------------------- |
| Intent     | Calculates scores for dbt models, now with conditional z-score application based on user preference. |
| Requirements | 1.1, 2.1                                                                         |

**Responsibilities & Constraints**
- Calculate raw scores for all models and assign to `DbtModel.raw_score`.
- If `apply_zscore` is `True`, calculate z-scores and assign to `DbtModel.score`.
- If `apply_zscore` is `False` (default), ensure `DbtModel.score` is set to a default or meaningful value (e.g., 0.0 or same as `raw_score` if z-score not calculated). For simplicity, it will be set to the z-score only if `apply_zscore` is true, otherwise it will be left as default 0.0 for `score` while `raw_score` will always be populated.

**Dependencies**
- Outbound: `DbtProject`, `DbtModel`

**Contracts**: Service

##### Service Interface
```python
class Scorer:
    # ... existing methods ...
    def score_project(self, project: DbtProject, apply_zscore: bool = False):
        """Scores all models in a project. Optionally applies Z-scores."""
        # ... logic to calculate raw scores ...
        # Assign raw_score to DbtModel.raw_score

        # If apply_zscore is True, calculate and assign z_scores to DbtModel.score
        # Otherwise, DbtModel.score remains its default value or is explicitly set to 0.0
```

### `modaryn`

#### `CLI`

| Field      | Detail                                                                                                |
| :--------- | :---------------------------------------------------------------------------------------------------- |
| Intent     | Command-line interface, now accepting a flag to control z-score application during score calculation. |
| Requirements | 1.2, 2.2                                                                                              |

**Responsibilities & Constraints**
- Parse the new `--apply-zscore` (or similar) CLI option.
- Pass the boolean value of `apply_zscore` to the `Scorer.score_project` method.

**Dependencies**
- Outbound: `Scorer`

**Contracts**: API

##### API Contract
| Method | Endpoint      | Request (relevant part)                               |
| :----- | :------------ | :---------------------------------------------------- |
| `modaryn` | `score` command | `--apply-zscore` (boolean, default=False, `-z` short option) |

### `modaryn/outputs`

#### `OutputGenerator` (and subclasses: `TerminalOutput`, `MarkdownOutput`, `HtmlOutput`)

| Field      | Detail                                                                                                        |
| :--------- | :------------------------------------------------------------------------------------------------------------ |
| Intent     | Generate reports, now displaying either raw or z-transformed scores and explicitly indicating the scoring mode. |
| Requirements | 2.1, 3.1                                                                                                      |

**Responsibilities & Constraints**
- Access the appropriate score (`raw_score` or `score`/`z_score`) from `DbtModel` instances based on an `apply_zscore` flag passed to `generate_report`.
- Include a clear indicator in the report (e.g., a header, a column label) whether z-scores were used for the displayed values.

**Dependencies**
- Inbound: `DbtProject`, `DbtModel`

**Contracts**: Service

##### Service Interface
```python
class OutputGenerator(ABC):
    # ... existing methods ...
    def generate_report(self, project: DbtProject, apply_zscore: bool = False, *args, **kwargs) -> Optional[str]:
        """Generates a report for the project. Score displayed depends on apply_zscore flag."""
        # Logic to decide which score to display (model.raw_score or model.score)
        # Logic to add a "Z-score applied" or "Raw Score" indicator in the report
```

## Data Models

#### `DbtModel`
Refer to the `DbtModel` component interface definition above. The introduction of `raw_score` and explicit use of `score` for z-score is the key change.

## Error Handling
Existing error handling for loading and scoring will be maintained. No new error handling specific to the z-score option is anticipated, beyond standard input validation.

## Testing Strategy

### Default sections (adapt names/sections to fit the domain)
- **Unit Tests**:
    - `Scorer` class: Add tests for `score_project` method to verify correct `raw_score` and `score` (z-score) assignment when `apply_zscore` is `True` and `False`.
    - `OutputGenerator` subclasses (`TerminalOutput`, `MarkdownOutput`, `HtmlOutput`): Add tests for `generate_report` to ensure correct score (`raw_score` vs `score`) is displayed and the z-score application indicator is present when `apply_zscore` is `True`.
- **Integration Tests**:
    - `CLI` `score` command: Write integration tests to execute the `modaryn score` command with and without the `--apply-zscore` flag, verifying the output content and format (specifically score values and z-score indicator).

## Supporting References (Optional)
- Detailed research and design rationale can be found in `.kiro/specs/optional-z-score/research.md`.
