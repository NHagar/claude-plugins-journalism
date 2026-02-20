# Schema Design Patterns for Document Extraction

Guidelines for designing extraction schemas that support investigative journalism workflows.

## Core Principles

### 1. Provenance First

Every record must trace back to its source:

```json
{
  "source_document": "foia_2024_001.pdf",
  "source_page": 3,
  "extracted_at": "2024-03-15T14:30:00Z"
}
```

### 2. Preserve Ambiguity

When data is unclear, preserve both the interpretation and the original:

```json
{
  "amount": 15000,
  "amount_raw": "$15,OOO",
  "amount_confidence": "medium",
  "amount_note": "OCR may have confused O for 0"
}
```

Confidence levels: `high`, `medium`, `low`, `uncertain`

### 3. Explicit Nulls

Distinguish between "not present," "redacted," and "illegible":

```json
{
  "name": null,
  "name_status": "redacted",
  "name_note": "Exemption b(6) cited"
}
```

Status values: `present`, `redacted`, `illegible`, `missing`, `not_applicable`


## Handling Inconsistent Tables

When tables vary across pages:

### Option 1: Union Schema
Combine all observed columns, mark missing as null:

```json
{
  "col_a": "value",
  "col_b": "value",
  "col_c": null,
  "col_c_status": "not_applicable",
  "col_c_note": "Column not present on this page"
}
```

### Option 2: Variant Schemas
Create separate schemas for different table formats:

```
documents_type_a.json  (pages 1-10)
documents_type_b.json  (pages 11-20)
```

Include a mapping file:
```json
{
  "schema_mapping": [
    {"pages": [1, 10], "schema": "documents_type_a"},
    {"pages": [11, 20], "schema": "documents_type_b"}
  ]
}
```

## Data Type Guidelines

| Data Type | Format | Example |
|-----------|--------|---------|
| date | ISO 8601 | `"2024-03-15"` |
| datetime | ISO 8601 with timezone | `"2024-03-15T14:30:00-05:00"` |
| currency | number + separate currency field | `{"amount": 1500.00, "currency": "USD"}` |
| boolean | true/false/null | `true` |
| enum | lowercase snake_case | `"released_partial"` |
| array | JSON array | `["item1", "item2"]` |

## Questions to Ask the Journalist

Before finalizing a schema, clarify:

1. **Granularity**: One record per row? Per page? Per document?
2. **Normalization**: Standardize names/dates, or preserve original formatting?
3. **Relationships**: Do entities need IDs for cross-referencing?
4. **Priority fields**: Which fields are essential vs. nice-to-have?
5. **Edge cases**: How to handle [specific ambiguity observed in document]?
6. **Output format**: Single JSON file, or split by schema/page range?