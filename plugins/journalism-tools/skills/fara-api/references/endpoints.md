# FARA API Endpoint Reference

Base URL: `https://efile.fara.gov/api/v1`

Every endpoint supports `html | csv | xml | json` — the format is a path segment, not a header. The JSON variant is what the client uses. Every endpoint 302-redirects to an internal ORDS/APEX URL — the client follows automatically.

## Table of contents

- [/Registrants/{fmt}/Active](#registrantsfmtactive)
- [/Registrants/{fmt}/Terminated](#registrantsfmtterminated)
- [/Registrants/{fmt}/New](#registrantsfmtnew)
- [/RegDocs/{fmt}/{reg}](#regdocsfmtreg)
- [/ShortFormRegistrants/{fmt}/{status}/{reg}](#shortformregistrantsfmtstatusreg)
- [/ForeignPrincipals/{fmt}/{status}/{reg}](#foreignprincipalsfmtstatusreg)
- [/Countries/{fmt}](#countriesfmt)  *(undocumented in official docs page)*
- [/DocumentTypes/{fmt}](#documenttypesfmt)  *(undocumented in official docs page)*

---

## /Registrants/{fmt}/Active

All currently active registrants.

**Envelope:** `REGISTRANTS_ACTIVE.ROW[]`
**Size:** ~560 rows as of writing.
**Fields (TitleCase_Snake):**

| Field | Type | Notes |
|---|---|---|
| Registration_Number | int | |
| Name | str | Registrant (firm or individual). Individuals are `"Last, First"`. |
| Address_1 | str | |
| City | str | |
| State | str | Usually US 2-letter but free-text |
| Zip | int \| str | Numeric for 5-digit zips, string when leading zeros ("01742") |
| Registration_Date | str | `MM/DD/YYYY` |

**Example row:**
```json
{
  "Registration_Number": 7715,
  "Name": "Smaili, Jihad M.",
  "Address_1": "2114 N. Broadway",
  "City": "Santa Ana",
  "State": "CA",
  "Zip": 92706,
  "Registration_Date": "04/14/2026"
}
```

---

## /Registrants/{fmt}/Terminated

All terminated registrants.

**Envelope:** `REGISTRANTS_TERMINATED.ROW[]`
**Size:** ~6,500 rows as of writing (grows forever; new terminations are appended).
**Fields:** same as `/Active` plus `Termination_Date` (`MM/DD/YYYY`).

---

## /Registrants/{fmt}/New

Registrants whose `Registration_Date` falls inside a window.

**Params:** `?from=MM-DD-YYYY&to=MM-DD-YYYY` (both required, hyphen-separated)
**Envelope:** `ROWSET.ROW[]`
**Fields (ALL_CAPS with XML-escaped spaces):**

| Raw key | Normalized (client strips `_x0020_`) | Notes |
|---|---|---|
| `REGISTRATION_x0020_NUMBER` | `REGISTRATION_NUMBER` | |
| `NAME` | `NAME` | |
| `BUSINESS_x0020_NAME` | `BUSINESS_NAME` | Often empty |
| `ADDRESS_x0020_1` | `ADDRESS_1` | |
| `ADDRESS_x0020_2` | `ADDRESS_2` | |
| `CITY` | `CITY` | |
| `STATE` | `STATE` | |
| `ZIP` | `ZIP` | |
| `REGISTRATION_x0020_DATE` | `REGISTRATION_DATE` | ISO 8601 w/ `T00:00:00` |
| `TERMINATION_x0020_DATE` | `TERMINATION_DATE` | ISO 8601 or empty string |

**Gotcha:** a window with zero matches returns HTTP 404 with the invalid-JSON error body — not an empty list.

---

## /RegDocs/{fmt}/{reg}

PDF filings for one registrant. This is the endpoint that produces the direct links to the PDFs on `efile.fara.gov/docs/`.

**Optional filters:**
- `?docType=<TOKEN>` — one of the 10 tokens from `/DocumentTypes/json`
- `?countryCode=<CC>` — 2-letter FARA code from `/Countries/json`
- Combinable: `?docType=AMENDMENT&countryCode=AF`

**Envelope:** `ROWSET.ROW[]`
**Fields:**

| Field | Notes |
|---|---|
| DATE_STAMPED | ISO 8601 with `T00:00:00` |
| REGISTRATION_NUMBER | |
| REGISTRANT_NAME | |
| DOCUMENT_TYPE | **Human form** like `"Exhibit AB"`, `"Amendment"` — not the filter token |
| URL | Public PDF URL, no auth needed to download |
| FOREIGN_PRINCIPAL_NAME | Empty string if not FP-specific |
| FOREIGN_PRINCIPAL_COUNTRY | Full country name (e.g. `"VENEZUELA"`), empty string otherwise |
| SHORT_FORM_NAME | Empty string if not short-form related |

**Example:**
```json
{
  "DATE_STAMPED": "2026-04-16T00:00:00",
  "REGISTRATION_NUMBER": 7715,
  "FOREIGN_PRINCIPAL_COUNTRY": "VENEZUELA",
  "DOCUMENT_TYPE": "Exhibit AB",
  "REGISTRANT_NAME": "Smaili, Jihad M.",
  "URL": "https://efile.fara.gov/docs/7715-Exhibit-AB-20260416-1.pdf",
  "SHORT_FORM_NAME": "",
  "FOREIGN_PRINCIPAL_NAME": "Delcy Eloina Rodriguez Gomez"
}
```

---

## /ShortFormRegistrants/{fmt}/{status}/{reg}

Short-form registrants (individuals filing under a registrant umbrella). `{status}` is `Active` or `Terminated`.

**Envelope:** `ROWSET.ROW[]`
**Fields:**

| Field | Notes |
|---|---|
| REG_NUMBER | Parent registrant's reg number |
| REGISTRANT_NAME | Parent registrant |
| SF_FIRST_NAME | |
| SF_LAST_NAME | |
| ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP | |
| REG_DATE | Parent registrant's registration date |
| SHORTFORM_DATE | When the short form was filed |
| SF_TERM_DATE | **Terminated variant only** |

---

## /ForeignPrincipals/{fmt}/{status}/{reg}

Foreign principals (the foreign clients) of one registrant. `{status}` is `Active` or `Terminated`.

**Envelope:** `ROWSET.ROW[]`
**Fields:**

| Field | Notes |
|---|---|
| REG_NUMBER | |
| REGISTRANT_NAME | |
| FP_NAME | Foreign principal (person or entity) |
| COUNTRY_NAME | **Full name**, not code (`"VENEZUELA"`, `"AFGHANISTAN"`) |
| ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP | |
| REG_DATE | Parent registrant's registration date |
| FP_REG_DATE | When the FP relationship was registered |

**No explicit termination-date field.** Active vs. terminated comes from the URL path alone.

---

## /Countries/{fmt}

**Not listed in the official endpoints page**, but referenced by the RegDocs filter docs. Enumerates the 265 country codes FARA uses for filter validation.

**Envelope:** `ROWSET.ROW[]`
**Fields:** `{COUNTRY_NAME, COUNTRY_CD}`
**Example rows:**
```json
[
  {"COUNTRY_NAME": "AFGHANISTAN", "COUNTRY_CD": "AF"},
  {"COUNTRY_NAME": "ALGERIA",     "COUNTRY_CD": "AG"},
  {"COUNTRY_NAME": "VENEZUELA",   "COUNTRY_CD": "VE"}
]
```

These are **not exactly ISO 3166-1 alpha-2**. Algeria is `AG` (ISO: `DZ`), for example. Always round-trip through this endpoint for filter values.

---

## /DocumentTypes/{fmt}

**Not listed in the official endpoints page.** Enumerates the 10 filter tokens accepted by `/RegDocs?docType=`.

**Envelope:** `ROWSET.ROW[]`
**Fields:** `{Document_Type}` (a single key per row — note: raw key is `Document_x0020_Type`; client normalizes)

**All values:**
- `AMENDMENT`
- `CONFLICT_PROVISION`
- `DISSEMINATION_REPORT`
- `EXHIBIT_AB`
- `EXHIBIT_C`
- `EXHIBIT_D`
- `INFORMATIONAL_MATERIALS`
- `REGISTRATION_STATEMENT`
- `SHORT-FORM`  *(note the hyphen, not underscore)*
- `SUPPLEMENTAL_STATEMENT`

**Mismatch warning:** the filter input uses these uppercase underscore tokens, but the `DOCUMENT_TYPE` value returned in RegDocs responses is human-readable (`"Exhibit AB"`, `"Amendment"`, `"Registration Statement"`, etc.). Don't try to filter by the response vocabulary.
