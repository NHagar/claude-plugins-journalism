---
name: document-extractor
description: Extract structured data from documents that resist standard parsing, such as redacted records, scanned forms, inconsistent tables, and OCR artifacts. Use this skill when a journalist needs to transform messy PDFs or images into structured JSON with full provenance tracking. Triggers on requests involving FOIA documents, court records, financial disclosures, government forms, leaked documents, or any document described as "hard to parse," "scanned," "redacted," or "inconsistent."
---

# Document Extractor for Investigative Journalism

Extract structured data from messy documents while maintaining provenance and human oversight.

## Workflow Overview

1. **Convert** → Transform document pages to images
2. **Transcribe** → Read each page image, output markdown preserving structure
3. **Stitch** → Combine markdown files with page delineators
4. **Schema** → Propose extraction schema(s), await journalist approval
5. **Extract** → Transform markdown to JSON using approved schema

## Step 1: Convert Document to Images

Run the conversion script:

```bash
uv run --with pdf2image --with pillow scripts/convert_to_images.py input.pdf --output-dir ./pages --dpi 300
```

Output: `pages/page_001.png`, `pages/page_002.png`, etc.

For image-based documents (TIFF, scanned images), copy directly to the pages directory with sequential naming.

## Step 2: Transcribe Each Page
**NOTE:** For large files (>50 pages), you need to use automated tooling, rather than reading all pages yourself. Refer to `references/automated-extraction.md` for details on that workflow. Otherwise, read and transcribe EVERY page yourself. Don't skip any.


Read the image file for each page in parallel. For each page image, output a markdown file preserving:

- **Layout**: Use tables, headers, indentation to mirror document structure
- **Redactions**: Mark as `[REDACTED]`
- **Illegible text**: Mark as `[ILLEGIBLE]` or `[UNCLEAR: partial text?]`
- **Handwriting**: Mark as `[HANDWRITTEN: transcription]` or `[HANDWRITTEN: ILLEGIBLE]`
- **Checkboxes**: Use `[X]` for checked, `[ ]` for unchecked
- **Stamps/signatures**: Note as `[STAMP: text]` or `[SIGNATURE]`

### Transcription Template

```markdown
<!-- Page N of document: filename.pdf -->
<!-- Document type: [form/letter/table/mixed] -->
<!-- Quality notes: [any OCR issues, damage, etc.] -->

[Transcribed content here, preserving structure]
```

### Example Transcription

```markdown
<!-- Page 1 of document: foia_response_2024.pdf -->
<!-- Document type: form -->
<!-- Quality notes: Slight skew, stamp partially cut off -->

# FREEDOM OF INFORMATION ACT REQUEST RESPONSE

**Date:** March 15, 2024
**Case Number:** FOIA-2024-00142
**Requester:** [REDACTED: ~2 words]

## Responsive Documents

| Doc ID | Date | Description | Pages | Disposition |
|--------|------|-------------|-------|-------------|
| A-001 | 2023-01-15 | Email correspondence | 3 | Released in full |
| A-002 | 2023-02-20 | [REDACTED] | 7 | Withheld (b)(6) |
| A-003 | [ILLEGIBLE] | Meeting notes | 2 | Released with redactions |

[STAMP: APPROVED FOR RELEASE - partially visible]
[SIGNATURE]
```

Save each transcription as `transcripts/page_001.md`, `transcripts/page_002.md`, etc.

## Step 3: Stitch Transcripts

Combine all page transcripts into a single file:

```markdown
# Full Document Transcript
**Source:** filename.pdf
**Total Pages:** N
**Processed:** YYYY-MM-DD

---

[Contents of page_001.md]

---
<!-- PAGE BREAK: 1 → 2 -->
---

[Contents of page_002.md]

...
```

Save as `full_transcript.md`.

## Step 4: Propose Schema(s)

Analyze the transcript and propose one or more schemas. Present to journalist for review.

### Schema Proposal Format

```markdown
## Proposed Extraction Schema(s)

### Schema 1: [Name]
**Applies to:** Pages X-Y (or "all pages," "pages containing tables," etc.)
**Purpose:** [What this schema captures]

| Field | Type | Description | Required | Example |
|-------|------|-------------|----------|---------|
| field_name | string/number/date/boolean/array | What it represents | Yes/No | "example value" |

### Schema 2: [Name]
...

## Open Questions for Review
1. [Question about ambiguous data]
2. [Question about handling edge cases]
3. [Question about field naming preferences]

## Notes
- [Any patterns observed]
- [Potential data quality issues]
- [Recommendations]
```

### Schema Design Principles

See `references/schema-patterns.md` for detailed guidance. Key principles:

- **Flat over nested** when possible for easier analysis
- **Consistent field names** across schemas (use snake_case)
- **Always include provenance**: `source_page`, `source_document`
- **Handle missing data explicitly**: use `null`, not empty strings
- **Preserve original text** alongside normalized values when ambiguous

**STOP HERE** - Present schema to journalist and await approval before proceeding.

## Step 5: Extract to JSON

After journalist approval, transform the markdown transcript to JSON. Do this YOURSELF, not with a script.

### Extraction Guidelines

1. **One JSON file per schema** if multiple schemas
2. **Array of records** at the top level
3. **Include metadata header**:

```json
{
  "extraction_metadata": {
    "source_document": "filename.pdf",
    "extraction_date": "2024-03-15",
    "schema_version": "1.0",
    "total_records": 42,
    "notes": ["Any extraction notes"]
  },
  "records": [
    {
      "source_page": 1,
      "field1": "value1",
      "field2": "value2"
    }
  ]
}
```

4. **Handle ambiguity transparently**:

```json
{
  "date": "2024-03-15",
  "date_raw": "3/15/24",
  "date_confidence": "high"
}
```

5. **Mark extraction issues**:

```json
{
  "name": null,
  "name_note": "REDACTED in source",
  "amount": 1500,
  "amount_note": "Partially illegible, interpreted from context"
}
```

### Output Files

Save to `output/` directory:
- `output/[schema_name].json` - Extracted data
- `output/extraction_report.md` - Summary of extraction with any issues

## File Structure
working_directory/
├── input.pdf                    # Original document
├── pages/                       # Page images
│   ├── page_001.png
│   └── ...
├── transcripts/                 # Individual page transcripts
│   ├── page_001.md
│   └── ...
├── full_transcript.md           # Stitched transcript
├── schema_proposal.md           # Schema for journalist review
└── output/
    ├── [schema_name].json       # Final extracted data
    ├── extraction_report.md     # Extraction summary
    └── review_[document].html   # Interactive review interface

## Step 6: Generate Review Interface

After extraction, generate a self-contained HTML review interface:

```bash
uv run scripts/generate_review_interface.py ./pages output/extracted.json \
    --output output/review_document.html \
    --document-name "FOIA Response 2024-001"
```

This creates a single HTML file the journalist can open in any browser—no server, no installation, no technical setup required.
