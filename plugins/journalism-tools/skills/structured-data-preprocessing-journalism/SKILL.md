---
name: journalistic-data-preprocessing
description: "Preprocessing workflow for journalistic data analysis emphasizing transparency, provenance, and human oversight. Use when: (1) Loading messy data files (Excel, CSV, JSON) into analysis-ready format, (2) Auditing data quality before analysis, (3) Cleaning data with full transformation documentation, (4) Preparing data for investigative journalism projects. Core principle: No silent transformations—every change is documented and approved."
---

# Journalistic Data Preprocessing

Preprocessing data for journalism requires higher standards than typical data science: every transformation must be traceable, every decision documented, and the human must approve substantive changes.

## Core Principles

1. **Provenance first**: Every row traces to source file, sheet, and row number
2. **No silent transformations**: Never automatically fix issues without documentation
3. **Human-in-the-loop**: Present findings and get approval before transformations
4. **Transparency artifacts**: Generate documentation a reporter could hand to an editor

## Workflow Overview

```
1. LOAD       → Ingest data, establish provenance columns
2. AUDIT      → Systematically examine every column for issues
3. REPORT     → Present findings, proposed fixes, questions to user
4. TRANSFORM  → After approval, execute documented transformations
5. VALIDATE   → Confirm transformations, output final dataset + audit trail
```

## Phase 1: Data Loading

### Architectural Questions to Ask User

Before loading, clarify:
- **Structure**: One table or multiple related tables?
- **Grain**: What does each row represent?
- **Key fields**: What uniquely identifies a record?
- **Time coverage**: What date range does this cover?

### Provenance Column Standard

Always add these columns to loaded data:

```python
'_source_file'    # Original filename
'_source_sheet'   # Sheet name (if Excel) or 'csv'
'_source_row'     # 1-indexed row number in original file
'_load_timestamp' # When this record was loaded
```

## Phase 2: Column Audit

Systematically examine **every column**.

### Audit Checklist Per Column

| Category | What to Check |
|----------|---------------|
| **Type** | Is inferred type correct? Mixed types? |
| **Missing** | How many nulls? Pattern to missingness? |
| **Cardinality** | Unique values vs total rows |
| **Distribution** | Outliers? Impossible values? |
| **Text quality** | Encoding issues? Entity variations? Typos? |
| **Dates** | Consistent format? Future or distant past dates? |
| **Numeric** | Scale consistent? Negative where unexpected? |

## Phase 3: Issue Report

Generate a report for human review. See `references/report-template.md` for format.

### Report Structure

```
# Data Quality Report: [Dataset Name]

## Summary
- Total rows / columns / columns with issues

## Critical Issues (Require Decision)
[Issues that could affect analysis validity]

## Warnings (Review Recommended)
[Issues that may or may not need fixing]

## Proposed Transformations
[Each transformation with rationale]

## Questions for Human Review
[Decisions that require domain knowledge]
```

### Key Report Principles

1. **Severity tiers**: Critical > Warning > Info
2. **Concrete examples**: Show actual problematic values
3. **Proposed fixes**: Suggest specific transformations
4. **Preserve optionality**: Let human choose between approaches
5. **Audit artifacts**: Identify what documentation to produce

## Phase 4: Transformations

After human approval, execute transformations with full documentation.

## Phase 5: Validation & Output

### Final Outputs

1. **Clean dataset** (`cleaned_[name].csv`) - Provenance columns preserved
2. **Transformation log** (`transformation_log.csv`) - Every change documented
3. **Audit report** (`data_audit_report.md`) - Issues, decisions, resolutions
4. **Entity mappings** (`entity_mapping_[column].csv`) - If standardization applied

## Human Review Artifacts

| Decision Type | Artifact to Generate |
|---------------|---------------------|
| Entity variations | Frequency table + proposed mapping |
| Outliers | Distribution summary + flagged values |
| Missing data | Missingness by column summary |
| Duplicates | Sample duplicate groups |

## References

- `references/report-template.md` - Full report template with examples
