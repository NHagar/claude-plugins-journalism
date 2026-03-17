# Analysis Playbook

Tactical reference for signal detection across datasets of varying scale. Read the
section that matches your data size, then use the technique catalog for specific
analysis approaches.

## Working with Large Data (1M+ rows)

The biggest mistake is trying to load everything into a pandas DataFrame. For datasets
above ~1M rows, default to DuckDB or SQLite for querying in place. These handle
multi-million-row files without memory issues.

### Strategy: Profile first, target second

1. **Use DuckDB to profile directly from files.** DuckDB reads CSV, Parquet, and JSON
   natively without loading into memory:
   ```python
   import duckdb
   con = duckdb.connect()

   # Row count without loading
   con.sql("SELECT count(*) FROM 'huge_file.csv'")

   # Column profiling
   con.sql("""
       SELECT
           column_name,
           count(*) as non_null,
           count(distinct column_name) as cardinality,
           min(column_name), max(column_name)
       FROM 'huge_file.csv'
       GROUP BY ALL
   """)
   ```

2. **Sample strategically, not randomly.** Random samples miss outliers by definition.
   Use multiple sampling strategies:

   - **Head/tail/middle**: Quick structural check. Are the first and last records
     different in character? (e.g., schema changes over time)
   - **Stratified**: Sample N records from each category of a key field. Ensures
     you see the full variety.
   - **Extreme values**: Pull the top and bottom N by each numeric column. This is
     where outliers live.
   - **Temporal slices**: If data has dates, sample from different time periods.
     Look for regime changes.
   - **Targeted**: Once you spot something interesting in aggregates, pull the
     specific records for inspection.

3. **Aggregate before you inspect.** Most signals in large data show up in aggregations
   (GROUP BY), not in individual records. Start with:
   - Counts and sums by category
   - Distributions (percentiles, histograms via NTILE or WIDTH_BUCKET)
   - Time series at appropriate granularity
   Then drill into individual records only for the groups that look anomalous.

### Memory management

- Never call `pd.read_csv()` on files over ~500MB without chunking
- Prefer DuckDB for any analytical query on large files
- If you must use pandas, use `dtype` specifications to reduce memory, and
  `usecols` to load only needed columns
- For iterative work, materialize intermediate results to Parquet (much smaller
  and faster than CSV) rather than holding everything in memory
- When generating summary statistics, write results to a small output table
  rather than trying to display millions of rows

## Working with Medium Data (100K–1M rows)

Pandas is fine here but be deliberate. Load once, profile immediately, then
work from the profile rather than re-scanning the full frame repeatedly.

Useful profiling one-liner:
```python
profile = df.describe(include='all').T
profile['null_pct'] = df.isnull().mean()
profile['nunique'] = df.nunique()
profile['dtype'] = df.dtypes
```

For text columns in medium data, don't try NLP on every row. Instead:
- Get value counts for categorical text (names, categories, statuses)
- Sample 100-200 rows for free-text fields and scan for patterns manually
- Use string operations (length, contains, regex) as cheap first filters

## Working with Small Data (<100K rows)

You can read everything. Do it. The danger here is under-analyzing, not
over-loading. Run a thorough pass:

1. Full descriptive statistics on every column
2. Cross-tabulations of categorical fields
3. Correlation matrix for numeric fields
4. Duplicate detection (full-row and key-field)
5. Temporal analysis if dates exist

## Working with Document Collections

**Critical: Do not skip document sources.** Agents consistently deprioritize PDFs and
semi-structured documents in favor of clean CSVs and spreadsheets. This is a known
failure mode. PDFs and document collections often contain entity-level detail,
methodological context, manufacturer or product names, narrative explanations, and
other information that structured data lacks. You must make a genuine extraction attempt
on every document source provided.

For PDFs, filings, or text documents:

1. **Inventory and classify first.** How many documents? What types? Any metadata
   (dates, sources, categories)? List every document explicitly.
2. **Attempt extraction on all documents, not just a sample.** For PDFs:
   - Try text extraction first (pdftotext, PyMuPDF, pdfplumber). Many "difficult"
     PDFs actually contain extractable text.
   - For tabular PDFs, use tabula-py or pdfplumber's table extraction.
   - For scanned/image PDFs, note the limitation explicitly but still attempt OCR
     if tools are available.
   - If extraction partially fails, work with what you got. Partial data from 16 PDFs
     is better than perfect data from 0 PDFs.
   - Log extraction quality for each document (clean, partial, failed) in your
     coverage notes.
3. **Build a structured dataset from extracted fields.** Dates, names, dollar amounts,
   addresses — anything that appears consistently across documents. This mini-dataset
   becomes analyzable alongside your structured sources.
4. **Sample for close reading.** Pick documents strategically (largest, smallest,
   newest, oldest, different categories) and read them carefully. Note any patterns
   in structure, language, or content.
5. **Use text search for hypothesis testing.** Once you have a hunch from sampling,
   grep/search across the full collection to see if the pattern holds.
6. **Cross-reference with structured data.** The most valuable analysis often comes from
   connecting document-extracted information to structured data — e.g., matching
   manufacturer names from PDFs to export volumes in CSVs.

## Technique Catalog

### Outlier Detection

**Numeric outliers:**
- IQR method: values below Q1-1.5*IQR or above Q3+1.5*IQR
- Z-score: values >3 standard deviations from mean (but skewed data breaks this)
- For skewed distributions (very common in financial/government data): use log
  transform first, or use percentile-based thresholds (e.g., top/bottom 1%)
- Domain-specific thresholds are often more useful than statistical ones (e.g.,
  contracts just below the bid threshold)

**Categorical outliers:**
- Values that appear only once or twice when most values appear hundreds of times
- Categories with unusual distributions on other fields
- Misspellings and near-duplicates (Levenshtein distance) that might be the same
  entity under different names

### Concentration Analysis

- Herfindahl-Hirschman Index (HHI) for market/allocation concentration
- Gini coefficient for distribution inequality
- Simple share analysis: what % of total does the top entity/category represent?
  Compare to what you'd expect if distribution were uniform.
- For geographic concentration: counts by geography normalized by population or
  another appropriate denominator

### Threshold Analysis

Suspicious patterns near known thresholds:
- Values clustering just below reporting thresholds (structuring)
- Values that are exact round numbers at unusual frequency
- Patterns of splitting (e.g., multiple transactions to the same entity
  that individually fall below a threshold but collectively exceed it)

Approach:
```sql
-- Histogram around a threshold (e.g., $10,000)
SELECT
    width_bucket(amount, 8000, 12000, 40) as bucket,
    count(*) as n
FROM transactions
GROUP BY 1
ORDER BY 1
```
Look for a spike just below and a dip just above.

### Temporal Analysis

**Start with the macro trend.** Before looking for spikes and anomalies, compute the
overall trajectory of the main metric (total volume, approval rate, dollar amount, count)
across the full time range of the dataset. Table or plot it at an appropriate granularity.
This is your first analytical act on any temporal data. The macro trend is often the lead
itself — a decade-long collapse, a steady surge, a sudden plateau. Don't bury it.

Once you have the big picture:
- Compare period-over-period (this month vs. same month last year)
- Look for activity at unusual times (weekends, holidays, after-hours)
- Identify "regime changes" — sudden shifts in volume, composition, or behavior
- Check for seasonality, and then look for deviations from the seasonal pattern
- Look for compositional shifts within the trend: even if total volume is flat, the
  mix of categories/entities/geographies may be changing significantly
- Check for rank-order changes over time: who was the top entity at the start of the
  data vs. the end? Rank reversals are often newsworthy even when the underlying
  numbers aren't statistical outliers

### Entity Resolution / Network Signals

- Shared attributes across records: same address, phone, officer, registered agent
- Look for entities that appear in multiple roles (e.g., both buyer and seller,
  both contractor and inspector)
- Cluster by shared attributes and look for unexpectedly large or densely connected
  clusters
- Name variations: sort alphabetically and scan for near-matches

### Contextual Significance (beyond statistics)

Statistical outlier detection (z-scores, IQR, percentile thresholds) finds what's
numerically unusual. But journalistic significance often depends on context that isn't
in the data. After your statistical passes, apply these lenses:

**Policy timeline overlay:** Identify any known policy changes, legislation, regulations,
or court decisions relevant to the dataset's domain. Map your temporal trends against
these events. Patterns that start, stop, or inflect at policy boundaries are strong leads.
Even if you don't know the specific policies, note inflection points and flag them as
"something changed here — investigate what."

**Rank-order and competitive analysis:** Compute rankings over time. Which entities were
at the top at the start of the data, and which are at the top now? Rank reversals —
especially among entities that a domain expert would consider peers or competitors — are
frequently newsworthy even when the absolute numbers aren't statistical outliers.
Guatemala surpassing Brazil as a destination isn't a z-score anomaly, but it's a story.

**Geographic and demographic context:** Raw counts by geography are almost never the
story. Normalize by population, income, housing stock, or whatever denominator fits the
domain. But also consider: is the geographic distribution of this activity consistent with
what domain knowledge would predict? A pattern concentrated in regions with no obvious
connection to the activity is worth flagging.

**Known sensitivity areas:** Some data patterns matter because of what they represent in
the world, not because of their statistical properties. Apply what you know about the
domain. Arms flows to conflict zones, lending patterns by race, environmental violations
near vulnerable communities, safety incidents at facilities with prior histories — these
deserve scrutiny proportional to their potential impact, even if the numbers are modest.

**What's missing that should be there:** Domain knowledge helps you notice absences.
A major player missing from an industry dataset. A state absent from a federal program.
A category that should exist but doesn't. Statistical methods don't flag what isn't there.

### Data Quality as Signal

Sometimes the most interesting finding is about the data itself:
- Mandatory fields that are blank for a specific subset of records
- Date sequences with gaps (missing months, missing IDs in a sequence)
- Values that change in format partway through (suggests a system change
  or manual entry)
- Duplicate records — are they true duplicates or records that shouldn't match?
- Inconsistent categorization of the same entity

### Cross-table / Cross-file Analysis

When working with multiple related datasets:
- Check referential integrity: do all foreign keys actually resolve?
  Orphaned records are often interesting.
- Compare overlapping fields across tables for consistency
- Look for entities present in one table but absent in a related one
  where you'd expect them
- Temporal alignment: do the date ranges match? Are there periods covered
  by one dataset but not the other?

## Anti-patterns to Avoid

- **The fishing expedition report.** Don't report every mildly unusual number.
  Apply judgment — if you found 200 "anomalies," your threshold is too low.
  Aim for 3-8 leads per tipsheet.

- **The correlation dump.** "Column A correlates with Column B" is not a lead
  unless you can explain why that's surprising or consequential.

- **The denominator problem.** Big numbers mean nothing without context.
  "$5M in contracts" is meaningless unless you know the total contract volume.
  Always compute shares, rates, or per-capita figures.

- **Survivorship bias.** You're analyzing what's in the data. Think about
  what's NOT in the data that should be.

- **Ignoring data generation.** Understand how the data was created. A "spike"
  in records might just mean someone did a batch upload. A "gap" might mean the
  system was down. Ask about provenance.

- **Satisficing on structured data.** If the source material includes both CSVs and
  PDFs, or both databases and document collections, you must analyze all of them.
  Agents consistently gravitate toward the cleanest structured source, produce findings
  from it, and then either skip or superficially acknowledge the rest. This misses entire
  categories of leads (e.g., manufacturer-level analysis that only exists in PDFs, or
  narrative context that explains a statistical pattern). Partial extraction from a hard
  source is worth more than no extraction.

- **Statistical significance without journalistic significance.** A z-score of 4.5 is
  interesting, but "this country went from #3 to #1 in five years" might be a better
  lead even if it doesn't register as a statistical outlier. Always ask: would a reporter
  who covers this beat find this surprising or important? If you can't answer that
  question, flag it as a question for the journalist rather than ignoring the pattern.
