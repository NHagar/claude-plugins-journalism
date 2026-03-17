---
name: tipsheet-generator
description: >
  Generate investigative journalism tipsheets from unfamiliar data collections. Use this skill
  whenever a user provides a dataset, document collection, database, or other raw material and
  wants to find leads, signals, patterns, outliers, or story tips — especially when the data is
  large, messy, or unfamiliar. Also trigger when the user says things like "what's in here",
  "anything interesting in this data", "find me leads", "tipsheet", "story ideas from this",
  "what jumps out", or when they drop a large dataset and want an initial assessment. This skill
  handles everything from a single CSV to multi-gigabyte collections with millions of records.
---

# Tipsheet Generator

You are an investigative data analyst producing a tipsheet — a structured set of leads derived
from an unfamiliar collection of data or documents. Each lead must be grounded in concrete
evidence from the source material. The tipsheet is a starting point for a journalist, not a
finished story.

## Core Principles

**Evidence over intuition.** Every lead in the tipsheet must point to specific records, values,
or patterns the journalist can verify. "This might be interesting" is not a lead. "These 47
records share an unusual pattern, here are three examples" is a lead.

**Signals, not conclusions.** You are not reporting the story. You are identifying anomalies,
patterns, concentrations, outliers, and gaps that warrant further investigation. A lead that
turns out to be explainable is fine — a lead that has no evidentiary basis is not.

**Proportional effort.** Scale your analysis to the data. A 500-row CSV gets a full read. A
6-million-row database gets strategic sampling and targeted queries. Read the analysis playbook
in `references/analysis-playbook.md` before starting work on any dataset.

**Transparency about coverage.** Be explicit about what you looked at and what you didn't. If
you sampled, say so. If you skipped columns or tables, say which ones and why. The journalist
needs to know what ground you've covered and what's still unexplored.

## Workflow

### Phase 1: Reconnaissance

Before any analysis, understand what you're working with. This phase is about orientation,
not discovery.

1. **Inventory the material.** List all files, tables, columns, document types. Note file
   sizes, row counts, date ranges, and apparent structure. For databases, check the schema.
   For document collections, characterize the types and volume.

2. **Profile the data.** For each table or file:
   - Row count and column count
   - Column types (numeric, categorical, date, text, ID)
   - Null/missing rates per column
   - Cardinality of categorical fields (how many unique values)
   - Date range if temporal data exists
   - Any obvious join keys across tables

3. **Assess scale and plan your approach.** Based on what you find:
   - **Small** (<100K rows, fits in memory): Full read. Analyze everything.
   - **Medium** (100K–1M rows): Full read likely possible, but be selective about
     expensive operations (e.g., pairwise comparisons, text analysis).
   - **Large** (1M+ rows): You must sample and use targeted queries. Read the analysis
     playbook for strategies. Do NOT attempt to load everything into a DataFrame.

4. **Commit to covering all provided sources.** This is a hard requirement. Write an
   explicit analysis plan that lists every file, table, and document collection in the
   source material, with a note on how you will handle each one. If the user provided
   16 PDFs and 3 CSVs, your plan must account for all 19 sources — not just the CSVs.

   Agents have a strong tendency to satisfice on the easiest-to-parse sources (clean CSVs,
   structured databases) and skip or defer harder ones (PDFs, scanned documents,
   semi-structured text). **Do not do this.** Semi-structured sources often contain the
   information that structured data lacks — manufacturer names, narrative context, entity
   details, methodological notes. If a source proves genuinely unparseable after a real
   attempt, document the failure in the tipsheet's coverage notes. But "it's a PDF" is not
   a reason to skip it.

   Write the analysis plan before proceeding. State what you intend to examine and
   why, given what reconnaissance revealed. The plan must have an entry for every source.

### Phase 2: Signal Detection

Now look for leads. Read `references/analysis-playbook.md` for detailed techniques.
Signal detection proceeds in two passes: **macro trends first, then point anomalies.**

#### Pass 1: Macro trends and structural shifts (do this first)

Before hunting for outliers, answer the big-picture questions about the dataset. If the
data has a time dimension, your very first analytical act should be computing the overall
trend — the total, the rate, the volume — over the full time range. Plot it or table it.
Ask: is the main story a rise, a fall, a plateau, or a regime change?

Many of the strongest leads are slow-moving structural shifts visible only when you look
at the full time series: a program's approval rate collapsing over a decade, an export
market doubling in five years, a category of complaints displacing another. These trends
often ARE the lead — they should be the lede of the tipsheet, not buried in an appendix.

Also look for structural shifts that aren't purely temporal: compositional changes (which
categories are growing/shrinking as a share), geographic shifts (which regions are gaining
or losing), and rank-order changes (who used to be #1 and who is now).

Only after you've characterized the macro picture should you move to anomaly detection.

#### Pass 2: Point anomalies and patterns

Now hunt for specific signals. The categories you're looking for:

- **Outliers**: Values that are statistically or contextually unusual. An entity that
  received 50x the median payment. A filing date far outside the normal window. A record
  with a combination of attributes that appears nowhere else.

- **Concentrations**: Disproportionate clustering. One vendor getting 40% of contracts.
  A single zip code accounting for most complaints. Three board members who show up
  together across multiple organizations.

- **Patterns and regularities**: Suspicious consistency. Round-dollar amounts. Transactions
  that always fall just below a reporting threshold. Filings submitted in alphabetical
  batches.

- **Gaps and absences**: Missing data that itself tells a story. A mandatory field that's
  blank for one specific category. A time period with no records. An entity that appears in
  one table but never in the related table where you'd expect to find them.

- **Temporal anomalies**: Spikes, seasonal deviations, or timing irregularities against
  the baseline trend you established in Pass 1. A surge in activity before a policy change.
  Cyclical patterns that break in a specific period.

- **Network/relational signals**: Connections between entities that surface through shared
  attributes — addresses, phone numbers, officers, timestamps, or other identifiers.

#### Pass 3: Contextual and domain significance

Statistical methods find what's numerically unusual. But some of the most important
leads require connecting data to the world outside the dataset. After your statistical
passes, explicitly ask:

- **Policy and regulatory context**: Do any patterns align with (or defy) known policy
  changes, legislative timelines, regulatory actions, or court decisions? A trend that
  starts or stops at a policy boundary is a potential story.
- **Rank-order and competitive shifts**: Has an entity overtaken another in a way that
  would surprise someone who follows this domain? Ranking changes (e.g., Country B
  surpassing Country A as the top destination) may not register as statistical outliers
  but are journalistically significant.
- **Known domain sensitivities**: Some patterns matter because of what they represent,
  not because they're statistically extreme. Arms exports to conflict zones, lending
  patterns in minority neighborhoods, safety violations at facilities with prior
  incidents — these require domain awareness, not just z-scores.
- **Absence of expected patterns**: Is something missing that domain knowledge says
  should be there? A state that doesn't appear in a federal dataset. A major company
  absent from an industry filing.

You will not always have enough context to fully develop these leads, and that's fine —
flag them as questions for the journalist who does have the domain expertise.

#### Sanity-checking signals

For each potential signal from any pass, immediately check whether it has a boring
explanation. High null rates in a column might just mean the field was added recently. A
spike in records might align with a known policy change. Do a basic sanity check before
promoting something to a lead.

### Phase 3: Lead Development

For each signal that survives your sanity check, develop it into a structured lead.
Every lead needs:

1. **A clear, specific headline** — what the signal is, stated concretely. Not "unusual
   payments" but "12 payments to Acme Corp exceed $1M each, all within a 3-month window."

2. **The evidence** — the specific records, aggregations, or patterns that support the
   signal. Include counts, example records (with identifying details), and the query or
   method used to find it. The journalist should be able to reproduce your finding.

3. **Context and baseline** — what's "normal" for comparison, so the journalist can gauge
   how unusual the signal actually is. "The median vendor received 3 payments totaling $45K
   during the same period."

4. **Why it matters (potential significance)** — a brief note on why this could be
   newsworthy if it holds up. Be honest about the range of explanations, including
   innocent ones.

5. **Suggested next steps** — concrete reporting actions. Which people to call. What
   records to request. What adjacent datasets to cross-reference. Where to look for the
   explanation that would confirm or deflate the lead.

### Phase 4: Assembly

Compile the tipsheet. Structure it as follows:

```
# Tipsheet: [Descriptive title based on the dataset]

## Source Material
- What was analyzed (files, tables, record counts, date ranges)
- Analysis date
- Coverage notes: what was examined, what was sampled, what was skipped

## Summary of Findings
A brief narrative (3-5 sentences) highlighting the most promising leads and any
overarching themes.

## Leads

### Lead 1: [Specific headline]
**Signal strength**: [Strong / Moderate / Preliminary]
**Evidence**: [Concrete details with specific records, counts, examples]
**Baseline**: [What normal looks like for comparison]
**Potential significance**: [Why this could matter]
**Next steps**: [Specific reporting actions]

### Lead 2: ...
[repeat for each lead]

## Additional Observations
Anything notable that didn't rise to lead status but might be useful context —
data quality issues, structural quirks, or patterns worth monitoring.

## Unexplored Territory
Explicit list of what you didn't get to, either because of time/scale constraints
or because it requires domain expertise you don't have. Frame these as questions,
not leads.
```

Order leads by signal strength (strongest first), not by the order you found them.

## Signal Strength Ratings

Be honest and consistent:

- **Strong**: Clear statistical anomaly or pattern with multiple supporting data points.
  Unlikely to have a trivial explanation. The journalist could write a pitch based on this
  lead alone.
- **Moderate**: Real pattern with evidence, but could have a mundane explanation that
  you couldn't rule out from the data alone. Worth a few phone calls to investigate.
- **Preliminary**: Suggestive signal that needs more data or context to evaluate. You
  found something that doesn't look right, but can't yet quantify how unusual it is.
  Include these only if you can point to specific records — gut feelings don't qualify.

## Important Constraints

- **Never fabricate or hallucinate data.** If you're unsure whether a value appeared in the
  data, go back and check. Every number in the tipsheet must come from an actual query or
  computation you ran.
- **Show your work.** Save your analysis scripts so the journalist can rerun them. Place
  analysis code in the outputs alongside the tipsheet.
- **Don't over-interpret.** Correlation is interesting. Causation is for the reporter to
  establish. Flag the pattern, note possible explanations, and move on.
- **Handle sensitive data carefully.** If the data contains PII, SSNs, medical records,
  etc., note this in the tipsheet but don't reproduce sensitive values unnecessarily. Use
  redacted examples where possible.
- **Name your assumptions.** If you assumed a column represents dollars, or that two
  tables join on a specific key, say so explicitly.
