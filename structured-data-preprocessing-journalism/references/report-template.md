# Data Quality Report Template

Template and examples for generating human-review reports.

## Example Report

```markdown
# Data Quality Report: campaign_contributions_2024.xlsx

*Generated: 2024-03-15 14:32*

## Summary

- **Total rows**: 45,892
- **Total columns**: 18
- **Provenance columns**: 4
- **Critical issues**: 3
- **Warnings**: 7

## Critical Issues (Require Decision)

### 1. Entity Variations in `contributor_name` (HIGH PRIORITY)

Found 156 potential duplicate entities with spelling variations.

**Top variations requiring decision:**

| Variant 1 | Count | Variant 2 | Count | Similarity |
|-----------|-------|-----------|-------|------------|
| "JOHNSON, ROBERT" | 47 | "JOHNSON, ROBERT J" | 23 | 0.92 |
| "SMITH ENTERPRISES LLC" | 31 | "SMITH ENTERPRISES, LLC" | 18 | 0.97 |
| "ACME CORP" | 89 | "ACME CORPORATION" | 12 | 0.85 |

**Proposed action:** Generate standardization mapping for approval.

**Artifact needed:** `entity_mapping_contributor_name.csv` showing all 156 variation groups

---

### 2. Impossible Values in `contribution_amount`

Found 12 rows with negative contribution amounts.

| _source_row | contributor_name | contribution_amount |
|-------------|-----------------|---------------------|
| 4521 | "JONES, MARY" | -500.00 |
| 8934 | "ABC PAC" | -1000.00 |
| 12045 | "SMITH, JOHN" | -250.00 |

**Questions:**
- Are these refunds? Should they be flagged rather than removed?
- Should negative values be converted to positive with a `refund` flag?

---

### 3. Duplicate Records Detected

Found 234 exact duplicate rows (117 duplicate groups).

**Sample duplicate group (source rows 1523, 8901):**

| Field | Value |
|-------|-------|
| contributor_name | ANDERSON, MICHAEL |
| contribution_amount | 500.00 |
| contribution_date | 2024-01-15 |
| recipient | SENATE CAMPAIGN CMTE |

**Questions:**
- Are these true duplicates or legitimate repeat contributions?
- What key fields should define uniqueness?

## Warnings (Review Recommended)

### 1. Missing Values in `employer` (23.4% null)

- 10,742 rows have null employer
- Missingness correlated with `contribution_amount < 200` (correlation: 0.78)
- This may be expected (small donors don't report employer)

**Proposed action:** Flag but retain; add `_employer_missing` column

---

### 2. Date Format Inconsistency in `contribution_date`

Multiple formats detected:
- YYYY-MM-DD: 41,234 rows (89.8%)
- MM/DD/YYYY: 4,658 rows (10.2%)

**Proposed action:** Standardize all to YYYY-MM-DD format

---

### 3. Outliers in `contribution_amount`

Using IQR method (bounds: $0 - $5,847):

- 892 contributions exceed upper bound
- Maximum value: $500,000

**Note:** Large contributions may be legitimate (PAC contributions). Review but don't auto-remove.

---

### 4. Encoding Issues in `contributor_address`

Found 34 rows with mojibake characters:

| _source_row | Original Value |
|-------------|----------------|
| 2341 | "123 Main St, San JosÃ©" |
| 5672 | "Montréal" → "MontrÃ©al" |

**Proposed action:** Apply UTF-8 re-encoding fix

## Proposed Transformations

| # | Column | Transformation | Rows Affected | Approval Required |
|---|--------|---------------|---------------|-------------------|
| T1 | `contributor_name` | Apply entity standardization mapping | ~3,200 | YES - review mapping |
| T2 | `contribution_date` | Standardize to YYYY-MM-DD | 4,658 | YES |
| T3 | `contributor_address` | Fix encoding (UTF-8) | 34 | YES |
| T4 | `employer` | Add `_employer_missing` flag column | 10,742 | NO - non-destructive |
| T5 | (all) | Remove exact duplicates | 117 | YES - review sample |

## Questions for Human Review

1. **Entity standardization**: Should "SMITH ENTERPRISES LLC" and "SMITH ENTERPRISES, LLC" be merged? What about "ACME CORP" vs "ACME CORPORATION"?

2. **Negative amounts**: Are negative contribution amounts refunds? How should they be handled?

3. **Duplicate definition**: What fields define a unique contribution? Is `(contributor_name, amount, date, recipient)` sufficient?

4. **Large contributions**: Should contributions over $10,000 be flagged for additional verification?

5. **Missing employer**: Is the correlation with small contributions expected? Any concern about data quality?

## Next Steps

After reviewing this report:

1. Respond with decisions on Questions 1-5
2. Approve/modify proposed transformations T1-T5
3. Request any additional artifacts (e.g., full duplicate list, outlier distribution chart)

The transformation code will not be executed until explicit approval is received.
```
