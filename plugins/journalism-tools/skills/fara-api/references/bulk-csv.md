# FARA Bulk CSV Dumps

FARA publishes daily-refreshed full-dataset dumps at `https://efile.fara.gov/bulk/zip/`, separate from the `/api/v1/` JSON API. They're the right tool for any country-level or cross-registrant query — one download answers a question that would take 500+ rate-limited API calls.

The client exposes them via:

- `c.bulk_foreign_principals()` → `FARA_All_ForeignPrincipals.csv.zip`
- `c.bulk_registrants()` → `FARA_All_Registrants.csv.zip`
- `c.bulk_registrant_docs()` → `FARA_All_RegistrantDocs.csv.zip`
- `c.bulk_short_forms()` → `FARA_All_ShortForms.csv.zip`

Each method downloads+unzips+parses, caches the zip for 1 hour in `$TMPDIR/fara_bulk/`, and returns a list of dicts with column names normalized to `ALL_CAPS_SNAKE` (the raw CSV columns have spaces).

## FARA_All_ForeignPrincipals.csv — columns

| Column (normalized) | Raw CSV header | Notes |
|---|---|---|
| FOREIGN_PRINCIPAL_TERMINATION_DATE | `Foreign Principal Termination Date` | Empty string if active |
| FOREIGN_PRINCIPAL | `Foreign Principal` | FP name |
| FOREIGN_PRINCIPAL_REGISTRATION_DATE | `Foreign Principal Registration Date` | `MM/DD/YYYY` |
| COUNTRY_LOCATION_REPRESENTED | `Country/Location Represented` | Full name (e.g. `"VENEZUELA"`), not code |
| REGISTRATION_NUMBER | `Registration Number` | Parent registrant |
| REGISTRANT_DATE | `Registrant Date` | Parent registrant's registration date |
| REGISTRANT_NAME | `Registrant Name` | |
| ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP | `Address 1`, `Address 2`, ... | FP address |

**Filter active-only:** `[r for r in rows if not r["FOREIGN_PRINCIPAL_TERMINATION_DATE"]]`
**Filter by country (case-insensitive substring):** `[r for r in rows if "venezuela" in r["COUNTRY_LOCATION_REPRESENTED"].lower()]`

## FARA_All_Registrants.csv — columns

Includes both active and terminated in one file. Active/terminated is inferred from whether `TERMINATION_DATE` is empty.

Columns include: `REGISTRATION_NUMBER`, `NAME`, `REGISTRATION_DATE`, `TERMINATION_DATE`, `ADDRESS_1`, `ADDRESS_2`, `CITY`, `STATE`, `ZIP`.

## FARA_All_RegistrantDocs.csv — columns

Every PDF filing ever made, across every registrant. Use this instead of iterating `c.reg_docs(reg_num)` across all registrants.

Columns include: `REGISTRATION_NUMBER`, `REGISTRANT_NAME`, `DATE_STAMPED`, `DOCUMENT_TYPE`, `URL`, `FOREIGN_PRINCIPAL_NAME`, `FOREIGN_PRINCIPAL_COUNTRY`, `SHORT_FORM_NAME`.

## FARA_All_ShortForms.csv — columns

All short-form registrants (individuals filing under a registrant umbrella), active + terminated.

Columns include: `REG_NUMBER`, `REGISTRANT_NAME`, `SF_FIRST_NAME`, `SF_LAST_NAME`, `ADDRESS_1`, `ADDRESS_2`, `CITY`, `STATE`, `ZIP`, `REG_DATE`, `SHORTFORM_DATE`, `SF_TERM_DATE`.

## Caching & freshness

- Default cache dir: `$TMPDIR/fara_bulk/`
- Default freshness window: 3600 s (1 hour)
- Bypass: `c.bulk_foreign_principals(max_age_s=0)` or CLI `--force-refresh`
- Files are rebuilt daily by FARA; hourly caching is a fine default for interactive use

## When NOT to use bulk

- **You need filings filtered by `docType` or a specific single registrant's live data.** The JSON API's `/RegDocs/{reg}?docType=...` filter doesn't have a bulk equivalent.
- **You need sub-registrant detail** (e.g. address fields that the bulk schema flattens differently than the JSON schema). Cross-check against the JSON API for a specific reg number when precision matters.
- **You need "last-5-minute" freshness.** The bulk dumps are daily.
