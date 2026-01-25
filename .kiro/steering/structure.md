# Project Structure

## Organization Philosophy

The project follows a layered architectural pattern, separating concerns into distinct modules. This makes the codebase easier to understand, maintain, and extend. The primary entry point is the CLI, which orchestrates the flow of data through the layers.

## Directory Patterns

### `modaryn/loaders`
**Location**: `modaryn/loaders/`
**Purpose**: Responsible for loading and parsing data from the dbt project, such as `manifest.json` and `.sql` files.

### `modaryn/analyzers`
**Location**: `modaryn/analyzers/`
**Purpose**: Contains the logic for analyzing the loaded dbt models. This includes dependency analysis and SQL complexity analysis.

### `modaryn/domain`
**Location**: `modaryn/domain/`
**Purpose**: Defines the core data structures and business logic of the application.

### `modaryn/scorers`
**Location**: `modaryn/scorers/`
**Purpose**: Implements the scoring logic, which takes the analysis results and calculates complexity and importance scores.

### `modaryn/outputs`
**Location**: `modaryn/outputs/`
**Purpose**: Handles the presentation of the final scores to the user in various formats (e.g., terminal, HTML, Markdown).

### `modaryn/cli.py`
**Location**: `modaryn/cli.py`
**Purpose**: The main entry point of the application, defining the CLI commands and orchestrating the different components.

## Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`

## Code Organization Principles

- The `cli.py` module should not contain any business logic. It should only be responsible for parsing CLI arguments and calling the appropriate services.
- Each layer should only interact with the layers directly adjacent to it. For example, `loaders` should not directly call `scorers`.
- The `domain` layer should be independent of the other layers.

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
