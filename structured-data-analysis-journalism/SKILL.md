---
name: structured-data-analysis-journalism
description: Analyze preprocessed data for investigative journalism with full transparency. Use when a journalist has clean, preprocessed data ready for analysis and needs to identify patterns, anomalies, relationships, or statistical findings that support a story. Triggers include requests to analyze data, find patterns, identify outliers, cross-reference records, calculate statistics, or answer specific investigative questions. Complements the structured-data-preprocessing skill. Emphasizes simple, legible analyses over complex methods—every finding must be explainable to editors and defensible under scrutiny.
---

# Investigative Analysis

Analyze preprocessed data to surface findings that support investigative reporting. Every analysis must be simple enough to explain, transparent enough to verify, and documented enough to defend.

## Core Principles

1. **Simple beats clever.** A journalist must be able to explain your analysis to an editor in plain language. If you can't explain it simply, simplify it.
2. **Every number needs a source.** Any statistic, count, or finding must trace back to specific records the journalist can verify.
3. **Assumptions are claims.** Treat every analytical assumption as a claim that requires justification and journalist approval.
4. **Findings are hypotheses.** Analysis surfaces patterns worth investigating—it doesn't prove wrongdoing. Frame findings accordingly.
5. **Defensibility over sophistication.** A simple frequency count that holds up under scrutiny beats a complex model that can't be explained in court.

## Workflow

### Stage 1: Analysis Proposal

Before running any analysis, produce a brief report for journalist review. Save as `analysis_proposal.md`.

**Proposal Format:**

```markdown
# Analysis Proposal
**Investigation**: [Brief description]
**Data sources**: [List preprocessed files being analyzed]
**Date**: [Date]

---

## Proposed Analyses

### Analysis 1: [Descriptive title]

**Question**: What investigative question does this answer?

**Inputs**: 
- File: `filename.csv`
- Columns: `col_a`, `col_b`, `col_c`

**Method**: [Plain-language description of what will be computed. Be specific but accessible.]

**Output**: [What will be produced—table, list, summary statistic, etc.]

**Supports claim**: [What finding would allow the journalist to report—frame as "Evidence that..." or "Allows us to say..."]

**Assumptions**:
- [Assumption 1 and why it's reasonable]
- [Assumption 2 and why it's reasonable]

**Limitations**: [What this analysis cannot tell us]

**Open questions**: [Any decisions needed from journalist]

---

### Analysis 2: [Title]
[Same structure]

---

## Summary

| # | Analysis | Key output | Supports |
|---|----------|------------|----------|
| 1 | [Title] | [Output type] | [One-line claim] |
| 2 | [Title] | [Output type] | [One-line claim] |

---

**⏸️ AWAITING YOUR REVIEW**

Please confirm which analyses to proceed with, answer any open questions, and flag concerns.
```

**Proposal Guidelines:**
- Keep it brief.
- Lead with the investigative question, not the technical method.
- Be honest about limitations—what can't this analysis tell us?
- Frame "Supports claim" carefully: analysis provides evidence, not proof.
- 3-7 analyses is typical. If proposing more, consider phasing the work.

**STOP after generating the proposal.** Do not proceed until journalist explicitly approves.

### Stage 2: Execution

After approval, execute each approved analysis with full documentation.

**For each analysis:**

1. **Write documented code**
   - Use pandas or DuckDB (prefer DuckDB for large data)
   - Include comments explaining each step
   - Print intermediate counts so journalist can follow the logic

2. **Preserve verifiability**
   - Any aggregate finding must link to underlying records
   - Export supporting record lists alongside summary statistics
   - Include provenance columns (`source_file`, `source_row`) in all outputs

3. **Validate results**
   - Sanity-check totals (do counts add up?)
   - Spot-check edge cases
   - Flag any unexpected patterns encountered during analysis

4. **Document findings**
   - What was found (plain language)
   - Key numbers with record counts
   - Caveats and limitations
   - Records to verify (specific examples for journalist to check)

### Stage 3: Findings Report

After completing approved analyses, produce `analysis_findings.md`:

```markdown
# Analysis Findings
**Investigation**: [Title]
**Date**: [Date]
**Analyses completed**: [N of M proposed]

---

## Finding 1: [Headline-style summary]

**From Analysis**: [Which analysis produced this]

**Key result**: [The core finding in plain language]

**Supporting numbers**:
- [Statistic]: [Value] (N=[record count])
- [Statistic]: [Value] (N=[record count])

**Underlying records**: See `finding_1_records.csv` ([N] records)

**Verification examples**: [3-5 specific records the journalist should spot-check, with source file and row]

**Caveats**:
- [Important limitation or context]

**Story language**: [Draft sentence suitable for publication, appropriately hedged]

---

## Output Files

| File | Description | Records |
|------|-------------|---------|
| `finding_1_records.csv` | Records supporting Finding 1 | N |
| `summary_statistics.csv` | All computed statistics | N |

---

## Methodology Notes

[Brief, plain-language explanation of what was done, suitable for a methodology box or editor questions]
```

## Analysis Types

### Appropriate for Investigative Work

**Counting and aggregation**: Frequencies, totals, averages by category. Simple, defensible, easy to verify.

**Filtering and flagging**: Identify records meeting specific criteria (thresholds, date ranges, category matches).

**Cross-referencing**: Match records across datasets on shared identifiers. Document match rates and non-matches.

**Outlier identification**: Flag statistical outliers using simple methods (percentiles, standard deviations). Always report the threshold used.

**Time-based patterns**: Trends, seasonality, before/after comparisons. Clearly define time boundaries.

**Network/relationship mapping**: Who connects to whom through shared attributes. Keep visualizations simple.

### Use With Caution

**Statistical inference**: Significance tests, confidence intervals. Only if journalist understands and can explain p-values. Always report effect sizes alongside p-values.

**Predictive models**: Rarely appropriate. If used, focus on feature importance over predictions. Never claim a model "proves" anything.

**Text analysis**: Keyword extraction, categorization. Be transparent about false positive/negative rates.

### Avoid

**Black-box ML**: No neural networks or methods that can't be fully explained.

**Causal claims**: Analysis shows correlation and patterns, not causation. Never use causal language.


**Output files:**
- CSV for data (UTF-8 encoding, include headers)
- Markdown for narrative findings
- Include provenance columns in all outputs

## Red Flags

Stop and consult the journalist if you encounter:

- **Circular reasoning**: The analysis assumes what it's trying to prove
- **Cherry-picking risk**: Results depend heavily on threshold choices
- **Small numbers**: Findings rest on very few records (< 10)
- **Missing context**: You lack information needed to interpret results fairly
- **Confirmation bias**: All evidence points one direction—look for counterexamples