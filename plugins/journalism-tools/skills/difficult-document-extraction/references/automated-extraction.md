# Automated Extraction Workflow

For documents with **>50 pages**. Writes extraction code, validates against gold standards, then scales to full document.

## Workflow

### Step 1: Create Gold Standards

Sample 10 page images. Manually transcribe each into markdown. Read pages carefully—do not use automated tools for gold standards.

Based on the contents of these sample pages, propose a JSON schema that captures this data to the journalist for review. After their review and approval, transform the markdown sample pages into JSON following the schema.

Save each as `gold_page_N.json`.

### Step 2: Journalist Review of Gold Standards

Present samples for validation:

```
I've transcribed the 10 sample pages.

**Page 1:**
- Image: [page_1.png]
- Transcription: [gold_page_1.json]

[Repeat for each sample]

Please verify accuracy before I write extraction code.
```

**Wait for explicit approval.**

### Step 3: Write Extraction Code

Choose strategy based on document type:

**PDFs with text layer:** Use pdfplumber
```python
import pdfplumber
import json

def extract_page(pdf_path, page_num, schema):
    """Extract data from a single page."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        
        # Extract tables
        tables = page.extract_tables()
        
        records = []
        for table in tables:
            for row in table[1:]:  # Skip header
                record = map_row_to_schema(row, schema)
                records.append(record)
        
        return {
            "records": records,
            "metadata": {
                "page_number": page_num,
                "extraction_notes": None
            }
        }
```

**Scanned/image documents:** Use OCR
```python
import pytesseract
from PIL import Image
import json

def extract_page_ocr(image_path, schema):
    """Extract data from page image using OCR."""
    img = Image.open(image_path)
    
    # Get OCR data with bounding boxes
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    
    # Group text into rows/columns based on position
    rows = group_into_rows(data)
    
    records = []
    for row in rows:
        record = map_row_to_schema(row, schema)
        records.append(record)
    
    return records
```

**Handling redactions:**
- Detect black rectangles by color/position
- Set fields to `null` when within redacted regions
- Set `is_redacted: true` for fully redacted rows

### Step 4: Validate Against Gold Standards

Compare automated output to gold standards field-by-field.

```python
import json

def compare_extraction(automated_path, gold_path):
    """Compare automated extraction against gold standard."""
    with open(automated_path) as f:
        auto = json.load(f)
    with open(gold_path) as f:
        gold = json.load(f)
    
    differences = []
    
    auto_records = auto.get("records", [])
    gold_records = gold.get("records", [])
    
    if len(auto_records) != len(gold_records):
        differences.append(f"Record count: auto={len(auto_records)}, gold={len(gold_records)}")
    
    for i, (a, g) in enumerate(zip(auto_records, gold_records)):
        for field in g.keys():
            if a.get(field) != g.get(field):
                differences.append(f"Row {i+1}, {field}: auto='{a.get(field)}', gold='{g.get(field)}'")
    
    return differences
```

**Iteration loop:**

1. **Run** extraction on all sample pages
2. **Measure** performance against gold standards
   - Field-level accuracy per page
   - Overall match rate
   - Per-field error rate across all pages
3. **Diagnose error patterns** — categorize every difference:
   - Column boundary misalignment (off-by-one columns, merged cells)
   - OCR misreads (specific characters, fonts, sizes)
   - Redaction detection failures (false positives/negatives)
   - Multi-line cell handling (wrapped text, line breaks within fields)
   - Header/footer interference (repeated elements parsed as data)
   - Whitespace/formatting artifacts (extra spaces, stray characters)
   - Structural mismatches (wrong number of records, split/merged rows)
4. **Attack the highest-impact error category first.** For each category with errors:
   a. **Isolate** a minimal failing case (single page, single field)
   b. **Search** for targeted solutions — don't guess, look it up:
      - `pdfplumber [specific issue]` (e.g., `pdfplumber merged cells extraction`)
      - `pytesseract [specific error pattern]` (e.g., `pytesseract misreads dollar signs`)
      - `python pdf table extraction [alternative library]`
      - `[library] vs [library] for [document characteristic]`
      - Look for library-specific settings, preprocessing techniques, or alternative libraries entirely
   c. **Implement** the fix
   d. **Re-run on all samples** — confirm the fix improved the target category without regressing others
5. **Repeat from step 1** with updated code. Track accuracy across iterations:
   ```
   Iteration 1: 82% field accuracy (main issue: column alignment)
   Iteration 2: 91% field accuracy (fixed alignment; new issue: dollar amounts)
   Iteration 3: 97% field accuracy (fixed currency parsing; remaining: 2 OCR artifacts)
   ```
6. **If stuck (2 iterations without improvement on a specific issue):**
   - Try a fundamentally different approach (e.g., switch from table extraction to position-based parsing, or from pdfplumber to camelot/tabula)
   - Try preprocessing the input (deskew, threshold, resize for OCR; crop headers/footers for table extraction)
   - Search for the specific document characteristic causing trouble (e.g., `pdf extract table with vertical merged cells python`)
7. **If the alternate approach also fails**, document the issue as a known limitation and move on

**When to stop iterating:**
- 100% match on all sample pages
- Remaining differences are source-level ambiguity (e.g., genuinely illegible text in the scan) that no extraction method could resolve
- Two fundamentally different approaches have both plateaued at the same error
- Document any systematic errors that cannot be resolved, with specific page/field examples

### Step 5: Present Extraction Method for Approval

Before scaling, explain to journalist:

```
My extraction process is ready.

**Method:** [Position-based / OCR with column mapping / etc.]

**Accuracy on samples:**
- Page 1: 100% match (47/47 fields)
- Page 47: 98% match (2 fields differ due to OCR artifacts)
- Page 203: 100% match
[etc.]

**Known limitations:**
- [e.g., "Handwritten annotations may extract incorrectly"]
- [e.g., "Heavily redacted rows appear with all null fields"]

**Output format:** JSON following approved schema

**Estimated time:** ~X minutes for Y pages

Should I proceed?
```

**Wait for approval.**

### Step 6: Run Full Extraction

```python
def extract_full_document(pdf_path, output_dir):
    """Extract all pages from document."""
    from pypdf import PdfReader
    
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    all_records = []
    page_stats = []
    
    for page_num in range(1, total_pages + 1):
        result = extract_page(pdf_path, page_num, schema)
        
        for record in result["records"]:
            record["_source_page"] = page_num
            all_records.append(record)
        
        page_stats.append({
            "page": page_num,
            "records": len(result["records"]),
            "notes": result["metadata"].get("extraction_notes")
        })
    
    # Save complete output
    output = {
        "records": all_records,
        "extraction_stats": {
            "total_pages": total_pages,
            "total_records": len(all_records),
            "pages_with_notes": [p for p in page_stats if p["notes"]]
        }
    }
    
    with open(f"{output_dir}/full_extraction.json", "w") as f:
        json.dump(output, f, indent=2)
    
    return output
```

### Step 7: Deliver Results

Provide journalist with:

1. **Complete output file** (`full_extraction.json`)

2. **Summary statistics:**
   - Total records
   - Redaction rate
   - Pages with extraction notes

3. **Edge cases for spot-checking:**
   - Pages with extraction notes
   - Pages with unusual record counts
   - First/last pages

```
Extraction complete.

**Results:**
- Total pages processed: [N]
- Total records extracted: [X]
- Fully redacted rows: [Y] ([Z]%)

**Output:** full_extraction.json

**Recommended spot-checks:**
- Page 47: extraction note about merged cells
- Page 156: unusual record count (12 vs typical 8)
- Pages 1, 100, 200, [last]: boundary pages

The extraction code is saved in case you need to re-run or modify.
```