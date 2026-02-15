# Requirements Document

## Introduction
This document outlines the requirements for introducing an optional z-score transformation to the `modaryn` scoring system. The primary goal is to allow users to analyze scores with standardized metrics while maintaining the raw scores as the default view.

## Requirements

### 1. Z-score Transformation Option
**Objective:** As a user, I want to optionally apply z-score transformation to the scores, so that I can analyze scores with standardized metrics.

#### Acceptance Criteria
1.  Where z-score option is enabled, the `modaryn` system shall apply z-score transformation to the calculated scores.
2.  The `modaryn` system shall provide a mechanism to enable or disable the z-score option.

### 2. Default Score Presentation
**Objective:** As a user, I want to see the raw scores by default, so that I can understand the original metrics without transformation.

#### Acceptance Criteria
1.  While z-score option is disabled, the `modaryn` system shall present the calculated scores without z-score transformation.
2.  The `modaryn` system shall, by default, have the z-score option disabled.

### 3. Z-score Application Indication
**Objective:** As a user, I want to know if z-score transformation has been applied, so that I can correctly interpret the presented scores.

#### Acceptance Criteria
1.  When scores are presented, the `modaryn` system shall clearly indicate whether z-score transformation has been applied.
