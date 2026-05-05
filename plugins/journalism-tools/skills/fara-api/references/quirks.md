# FARA API quirks

Things the client handles but you should know exist when debugging, extending the client, or building anything downstream that touches raw responses.

## 1. Rate limit: 5 requests per rolling 10 seconds

Shared across all endpoints. Exceeding returns HTTP 429 with body `Error Code: 429 | Description: Request rate too high`. The 10-second window is a sliding window, not aligned to clock seconds. The client uses a `collections.deque` of timestamps and sleeps until the oldest one ages out when needed.

If you add a retry layer, use exponential backoff starting at 10+ seconds for 429 — anything shorter risks re-tripping the limiter immediately.

## 2. Every public endpoint 302-redirects

The public `/api/v1/...` URLs all 302 to an internal ORDS/APEX endpoint that looks like:

```
https://efile.fara.gov/CallAPI/GetJSON?a=f?p=API:REGISTRANTDOCS-F_XML:::::F_XML_REG_NUM,F_XML_CC,F_XML_DOC_TYPE:7715,VE,
```

The trailing comma-separated positional params encode whatever query params you passed. `urllib.request.urlopen` follows redirects by default; `requests.get` does too; `curl` needs `-L`; some HTTP clients (e.g. older Go stdlib or naive `fetch` wrappers with `redirect: 'manual'`) do not.

## 3. Envelope key varies by endpoint

| Endpoint | Top-level wrapper |
|---|---|
| `/Registrants/Active` | `REGISTRANTS_ACTIVE` |
| `/Registrants/Terminated` | `REGISTRANTS_TERMINATED` |
| Everything else | `ROWSET` |

Why the inconsistency? The older Registrants endpoints appear to have been retrofitted into the ORDS pipeline with different XML→JSON bindings than the newer ones. The client normalizes by picking the first wrapper it recognizes.

## 4. Field-name casing varies by endpoint

Three distinct styles in the same API:

| Endpoint | Style | Example |
|---|---|---|
| `/Registrants/Active`, `/Registrants/Terminated` | `TitleCase_Snake` | `Registration_Number`, `Name` |
| `/Registrants/New` | `ALL_CAPS` with XML-escaped spaces in keys | `REGISTRATION_x0020_NUMBER`, `BUSINESS_x0020_NAME` |
| `/RegDocs`, `/ForeignPrincipals`, `/ShortFormRegistrants`, `/Countries`, `/DocumentTypes` | plain `ALL_CAPS_SNAKE` | `REGISTRATION_NUMBER`, `REGISTRANT_NAME` |

The `x0020` is the XML character reference for a space (U+0020) being passed straight through whatever XML-to-JSON transformer ORDS uses — the source column names contain literal spaces, and the transformer encoded them rather than replacing them. The client does `re.sub(r'_x0020_', '_', key)` to normalize.

## 5. Single-row results come back as an object, not an array

When the underlying query returns exactly one row, `ROW` is a dict. When it returns multiple, `ROW` is a list. Zero rows → see next quirk.

```json
// single row
{"ROWSET": {"ROW": {"REG_NUMBER": 7715, ...}}}

// multiple rows
{"ROWSET": {"ROW": [{"REG_NUMBER": 7715, ...}, {"REG_NUMBER": 7715, ...}]}}
```

This is the standard Oracle APEX XML-to-JSON transform behavior. The client coerces dict → `[dict]` so callers always see a list.

## 6. Empty result body is a string, not a missing field

```json
{"ROWSET": ""}
```

Not `null`, not `{}`, not `{"ROW": []}`. Literally the empty string. Test with `inner in ("", None)` before trying to read `.ROW`.

## 7. Error body is invalid JSON

When the backend has no data for a lookup or a param is bad, you get this body verbatim:

```
{ Success: false, Message: "Error loading API - Unable to retrieve data set" }
```

Unquoted keys → `json.loads` raises `JSONDecodeError`. The client detects this by string-matching `Success:` and `false` in the first ~120 bytes (both because `json.loads` fails first and because we want to extract the message for the exception).

## 8. HTTP status codes are ambiguous

- **404** is returned for:
  - A registrant that exists but has no records for the given sub-endpoint (e.g. `/ShortFormRegistrants/Active/6924` when that firm has no active short-form filers)
  - A `/Registrants/New` window with zero matches
  - *Possibly* also for malformed paths, but hard to tell — every "bad" result uses the same body.
- **500** is also returned for some no-data cases (e.g. `/ForeignPrincipals/Terminated/6924` with no terminated FPs).
- **200** is returned on success, including for the `{"ROWSET": ""}` empty-result case.

Implication: don't treat 404 as "endpoint doesn't exist." The client raises `FaraApiError` for both 404 and 500 with the message embedded, letting the caller decide.

## 9. Date formats differ across endpoints

- `/Registrants/Active` and `/Registrants/Terminated`: `MM/DD/YYYY` (slash, no time)
- `/Registrants/New` (query param): `MM-DD-YYYY` (hyphen, required)
- `/Registrants/New` response dates, `/RegDocs`, `/ForeignPrincipals`, `/ShortFormRegistrants`: ISO 8601 with `T00:00:00` (e.g. `"2026-04-14T00:00:00"`)

If you're normalizing, be prepared for both.

## 10. Encoding

Docs say `iso-8859-1`. In practice the response bytes for the English-dominant dataset have mostly been ASCII-clean, but names can include accented characters (e.g. `"Delcy Eloina Rodríguez"`). The client decodes as `iso-8859-1` defensively. If you serialize to UTF-8 downstream, you're fine — every iso-8859-1 code point has a UTF-8 representation.

## 11. No server-side search, filtering, pagination, or incremental cursor

Your only query levers are:
- The registrant number (path param on all per-registrant endpoints)
- `from` / `to` date window on `/Registrants/New`
- `docType` / `countryCode` on `/RegDocs`

No `limit`, no `offset`, no `since`, no name search, no full-text. To build anything incremental you must dump all-active periodically and diff.
