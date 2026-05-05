---
name: fara
description: Query the US DOJ Foreign Agents Registration Act (FARA) public eFile API — look up registrants, their foreign principals, short-form registrants, and PDF filing URLs. Use whenever the user mentions FARA, FARA.gov, efile.fara.gov, foreign agents, foreign-principal filings, foreign lobbying disclosures, or needs to enrich people/company records with FARA registration data, even when they don't explicitly say "FARA API".
---

# FARA API

Query the public FARA eFile API at `https://efile.fara.gov/api/v1`. No auth. Rate-limited to 5 requests per rolling 10 seconds.

## When to use this skill

- Any request about FARA, FARA.gov, efile.fara.gov, or "foreign agents" in the US disclosure sense
- Looking up who is registered as a foreign agent for a given country or foreign principal
- Finding PDF filings (registration statements, amendments, supplemental statements, exhibits A/B/C/D, dissemination reports, conflict-provision filings, informational materials)
- Enriching a list of firms/individuals with FARA registration status
- Investigative, compliance, or OSINT workflows around foreign influence and lobbying

## How to use

`scripts/fara_client.py` is the entrypoint. It wraps every endpoint, handles the rate limit, follows the internal redirect to the ORDS/APEX backend, retries transport errors + 5xx responses with exponential backoff, and normalizes the API's several schema quirks into plain Python lists of dicts. **Always use it — do not hand-call curl.** The API's response shape is surprising in ways the client hides.

The client is stdlib-only — no `pip install` needed.

## Pick the right data path — this matters a lot

FARA exposes TWO data paths. Pick based on your query shape:

| Query shape | Data path | Why |
|---|---|---|
| "Everything about registrant N" (one registrant, one or two sub-entities) | **Per-endpoint JSON API** (`reg_docs`, `foreign_principals_active`, etc.) | Fast, live. 1-3 calls. |
| "Who is currently registered for country X?" or anything that requires scanning all registrants | **Bulk CSV download** (`bulk_foreign_principals`, `bulk_registrants`, etc.) | **ONE HTTP download** (<1 MB, refreshed daily). Iterating all 560+ active registrants via the per-endpoint API takes ~20 minutes at 5 req / 10 s; the bulk CSV answers the same question in seconds. |
| "Every PDF filing across all registrants" | `bulk_registrant_docs` | Same reason: one download vs. thousands of calls. |
| "Find a registrant by name" | `search_registrants.py` (which uses the bulk Registrants list) | Also a bulk-scan problem; no server-side search exists. |

**If your first instinct is to loop over `list_active()` and call a per-registrant method inside that loop, STOP.** Use `bulk_foreign_principals()` or another bulk method instead. The only time looping over registrants is the right call is when each registrant needs a different, targeted follow-up (e.g. `reg_docs` with a specific `docType` filter that the bulk file doesn't support).

### CLI examples

**Per-registrant (JSON API):**
```bash
# Everything about one registrant: active+terminated FPs, short forms, and all filings
uv run scripts/fara_client.py profile 7715

# PDF filings filtered by country and/or document type
uv run scripts/fara_client.py regdocs 7715 --country-code VE --doc-type EXHIBIT_AB

# Active registrants listing (no FPs) — ~560 rows in one call
uv run scripts/fara_client.py list-active

# Registrants whose Registration_Date falls in a window (dates are MM-DD-YYYY)
uv run scripts/fara_client.py list-new --from 01-01-2025 --to 12-31-2025

# Lookup tables
uv run scripts/fara_client.py list-countries
uv run scripts/fara_client.py list-doc-types
```

**Cross-registrant / country queries (bulk CSV):**
```bash
# Every active Venezuela-linked FP in one shot (substring match on country)
uv run scripts/fara_client.py bulk-foreign-principals --country VENEZUELA --active-only

# Every PDF filing across every registrant
uv run scripts/fara_client.py bulk-registrant-docs

# Bypass the 1-hour local cache
uv run scripts/fara_client.py bulk-foreign-principals --force-refresh
```

**Name search (fuzzy, punctuation-insensitive):**
```bash
# All matches (active + terminated), ranked
uv run scripts/search_registrants.py "akin gump"

# Only the single best active match — exits 1 with a warning if ambiguous
uv run scripts/search_registrants.py --best-match "ogilvy"
```

### Python API

```python
import sys; sys.path.insert(0, "scripts")
from fara_client import FaraClient, FaraApiError

c = FaraClient()
for reg in c.list_active():
    fps = c.foreign_principals_active(reg["Registration_Number"])
    ...
```

All client methods return a normalized `list[dict]` (never the raw `ROWSET.ROW` envelope, never a bare dict for single-row results).

## Important behaviors the client handles for you

These bit us when writing the client — don't bypass the client and reintroduce them:

1. **Rate limiting.** 5 requests per rolling 10 seconds. Exceeding returns HTTP 429. The client throttles with a sliding-window limiter.
2. **Transport flakiness.** The ORDS/APEX backend regularly returns `Connection reset`, read-timeouts, and HTTP 500 under load. The client retries these with exponential backoff (up to 4 retries, starting at 2s). It does **NOT** retry 4xx — those are usually FARA's "no data" signal and retrying won't change the answer.
3. **Internal redirect.** Every public endpoint 302's to `/CallAPI/GetJSON?a=f?p=API:...`. `urllib` follows by default, but anything that doesn't must be told to.
4. **Wrapping key varies.** `/Registrants/Active` uses `REGISTRANTS_ACTIVE`, `/Registrants/Terminated` uses `REGISTRANTS_TERMINATED`, every other endpoint uses `ROWSET`.
5. **Field-name casing varies across endpoints.** `/Registrants/Active|Terminated` returns `TitleCase_Snake` (`Registration_Number`, `Name`). `/Registrants/New` returns `ALL_CAPS` with XML-escaped spaces baked into JSON keys (`REGISTRATION_x0020_NUMBER`, `BUSINESS_x0020_NAME`). `/RegDocs`, `/ForeignPrincipals`, `/ShortFormRegistrants` use plain `ALL_CAPS_SNAKE`. The client rewrites `_x0020_` → `_` so you just see `REGISTRATION_NUMBER`. The bulk CSV columns use spaces — the client normalizes to `ALL_CAPS_SNAKE` to match.
6. **Single-row results return as an object, not an array.** When the query yields one record, `ROW` is a dict; with multiple, it's a list. The client always coerces to a list.
7. **Empty set is `{"ROWSET": ""}`** (an empty string, not `null`, not `{}`, not `{ROW:[]}`). The client returns `[]`.
8. **Error body is literally invalid JSON.** FARA returns `{ Success: false, Message: "..." }` with unquoted keys — `json.loads` raises. The client detects this string pattern and raises `FaraApiError` with the embedded message.
9. **HTTP 404 is ambiguous.** It's returned for both "no data in this window" and genuinely-bad params. The client raises `FaraApiError` either way so the caller can inspect the message.

## Registrant-name ambiguity — flag it, don't paper over it

Registrant names in FARA are filed verbatim and are **frequently messy**. Be alert for:

- **Embedded punctuation breaks naive substring matching.** "Akin Gump" is stored as `"Akin, Gump, Strauss, Hauer & Feld, LLP"`. The skill's `search_registrants.py` normalizes punctuation before comparing, so this works — but if you're matching in your own code, normalize too.
- **Multiple reg numbers per firm.** Firms often hold several FARA registrations across the years (new entities, re-registrations after termination, sub-brands). Ogilvy has 3+ records; Dentons has 3. When a user asks "is firm X registered?", a single reg number may be misleading.
- **Misspellings and abbreviations.** "SKDK" vs "SKDKnickerbocker", accented characters in individual names, "Inc"/"Inc."/"LLC"/"LLP".
- **Individual names are `"Last, First M."`.** Substring match "Smith" will hit every Smith.

**Behavior to adopt:** when the user provides firm names and you run a search, surface **every match**, not just the top one. Report "found 3 records matching 'Dentons': #7087 (terminated 2022), #... " rather than silently picking one. `search_registrants.py --best-match` does this correctly — it exits 1 with a warning when the top match is ambiguous or only terminated records match. If you're writing custom CSV output "one row per input firm", pick the active record if one exists, else the most recent terminated — but always note the alternates in prose.

## Filter values for `/RegDocs`

`reg_docs()` accepts two optional filters:

- `doc_type` — one of 10 uppercase tokens (see `c.list_document_types()` or `references/doc-types.md`): `AMENDMENT`, `CONFLICT_PROVISION`, `DISSEMINATION_REPORT`, `EXHIBIT_AB`, `EXHIBIT_C`, `EXHIBIT_D`, `INFORMATIONAL_MATERIALS`, `REGISTRATION_STATEMENT`, `SHORT-FORM`, `SUPPLEMENTAL_STATEMENT`. Note the response field `DOCUMENT_TYPE` comes back in human form ("Exhibit AB", "Amendment") — different vocabulary than the filter input.
- `country_code` — 2-letter FARA code from `c.list_countries()`, matching the `COUNTRY_CD` field. These are close to but not identical to ISO 3166-1 alpha-2 (e.g. Algeria is `AG`, not `DZ`; Venezuela is `VE`).

The `/Countries` and `/DocumentTypes` endpoints are **not listed** on the official docs page; we discovered them by reverse-engineering filter-param validation. Treat them as authoritative for filter values.

## Detailed endpoint reference

- `references/endpoints.md` — full field list per JSON endpoint and example responses.
- `references/bulk-csv.md` — the 4 bulk CSV dumps, their columns, and when to use which.
- `references/quirks.md` — gory details on the schema inconsistencies.

## Remaining limits

- **No full-text search.** Bulk registrants + local filtering (`search_registrants.py`) is the workaround.
- **No pagination / incremental cursor on the JSON API.** Each call returns everything or nothing for its scope.
- **Bulk CSVs refresh once daily**, so for same-day filings you still need the JSON API.
- **Date format is inconsistent.** `/Registrants/New` params are `MM-DD-YYYY`; response fields are mixed — `MM/DD/YYYY` strings on some endpoints, ISO 8601 with a zero time component (`2025-12-31T00:00:00`) on others, and the bulk CSVs use `MM/DD/YYYY`.

## Output format expectations

When the user is asking a question (e.g. "who's lobbying for Venezuela?"), answer in prose with the relevant registrant names, reg numbers, and filing dates — not a raw JSON dump. When they explicitly ask for data for downstream use ("save as CSV", "put it in a dataframe", "give me the URLs"), use the Python API and write the result to a file.
