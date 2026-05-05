#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Client for the FARA eFile API (https://efile.fara.gov/api/v1).

Stdlib-only. Rate-limited (5 req / 10 s, sliding window). Normalizes the API's
varied response envelopes, coerces single-row results to a list, detects the
non-standard `{ Success: false, ... }` error body (which is not valid JSON),
and exposes both a Python API and a CLI.

Run `python fara_client.py --help` for CLI usage.
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Iterable

BASE_URL = "https://efile.fara.gov/api/v1"
BULK_URL = "https://efile.fara.gov/bulk/zip"


class FaraApiError(RuntimeError):
    """Raised for non-2xx HTTP status or FARA's `{ Success: false, ... }` error body."""


class _SlidingWindowLimiter:
    """5 requests per rolling 10 seconds, per the FARA docs."""

    def __init__(self, max_calls: int = 5, period_s: float = 10.0):
        self.max_calls = max_calls
        self.period_s = period_s
        self._calls: collections.deque[float] = collections.deque()

    def acquire(self) -> None:
        now = time.monotonic()
        while self._calls and now - self._calls[0] > self.period_s:
            self._calls.popleft()
        if len(self._calls) >= self.max_calls:
            sleep_for = self.period_s - (now - self._calls[0]) + 0.1
            if sleep_for > 0:
                time.sleep(sleep_for)
            now = time.monotonic()
            while self._calls and now - self._calls[0] > self.period_s:
                self._calls.popleft()
        self._calls.append(time.monotonic())


_REGISTRANT_ENVELOPES = ("REGISTRANTS_ACTIVE", "REGISTRANTS_TERMINATED", "ROWSET")
_X0020 = re.compile(r"_x0020_")


def _unwrap(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten FARA's varied envelopes into a list of row dicts.

    Handles:
    - REGISTRANTS_ACTIVE.ROW / REGISTRANTS_TERMINATED.ROW / ROWSET.ROW
    - ROW as a single dict (one record) or list of dicts (multiple)
    - Empty result: {"ROWSET": ""}  ->  []
    - x0020 (XML-escaped space) in JSON keys -> underscore
    """
    if not payload:
        return []
    inner: Any = None
    for wrapper in _REGISTRANT_ENVELOPES:
        if wrapper in payload:
            inner = payload[wrapper]
            break
    if inner is None:
        inner = next(iter(payload.values()), None)
    if inner in ("", None) or not isinstance(inner, dict):
        return []
    rows = inner.get("ROW")
    if rows is None:
        return []
    if isinstance(rows, dict):
        rows = [rows]
    return [{_X0020.sub("_", k): v for k, v in r.items()} for r in rows]


class FaraClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout_s: float = 60.0,
        limiter: _SlidingWindowLimiter | None = None,
        max_retries: int = 4,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self._limiter = limiter or _SlidingWindowLimiter()

    # ----- low-level request -----

    def _get(self, path: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if query:
                url = f"{url}?{query}"

        raw, status = self._request(url)
        text = raw.decode("iso-8859-1", errors="replace")

        # The error body is invalid JSON (unquoted keys). Detect by signature.
        stripped = text.lstrip()
        if stripped.startswith("{") and "Success:" in stripped[:80] and "false" in stripped[:120]:
            m = re.search(r'Message:\s*"([^"]*)"', text)
            msg = m.group(1) if m else text.strip()
            raise FaraApiError(f"FARA API error (HTTP {status}): {msg}")

        if status >= 400:
            raise FaraApiError(f"HTTP {status} from {url}: {text[:200]}")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise FaraApiError(f"Malformed JSON from {url}: {e} | body={text[:200]!r}")
        return _unwrap(payload)

    def _request(self, url: str) -> tuple[bytes, int]:
        """Execute a single request with rate limiting and retry-with-backoff.

        Retries on:
        - Transport errors: ConnectionResetError, socket.timeout, URLError
        - HTTP 5xx (server-side flakiness — the ORDS backend does this often)
        Does NOT retry on 4xx: FARA uses 404 as "no data" and retrying won't help.
        """
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._limiter.acquire()
            # Server 502s / resets on urllib's default User-Agent — send a browser-like one.
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": "Mozilla/5.0 (fara-skill-client)",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    return resp.read(), resp.status
            except urllib.error.HTTPError as e:
                body = e.read() if e.fp else b""
                if 500 <= e.code < 600 and attempt < self.max_retries:
                    last_exc = e
                    time.sleep(2 ** attempt + 1)
                    continue
                return body, e.code
            except (ConnectionResetError, socket.timeout, urllib.error.URLError, TimeoutError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise FaraApiError(f"Transport error after {self.max_retries + 1} attempts: {e}") from e
        # Unreachable but keeps type checkers happy
        raise FaraApiError(f"Exhausted retries: {last_exc}")

    # ----- endpoints: Registrants -----

    def list_active(self) -> list[dict[str, Any]]:
        """All active registrants.

        Fields: Registration_Number, Name, Address_1, City, State, Zip, Registration_Date.
        """
        return self._get("/Registrants/json/Active")

    def list_terminated(self) -> list[dict[str, Any]]:
        """All terminated registrants. Same fields as list_active plus Termination_Date."""
        return self._get("/Registrants/json/Terminated")

    def list_new(self, from_date: str, to_date: str) -> list[dict[str, Any]]:
        """Registrants whose Registration_Date falls in [from_date, to_date].

        Dates must be MM-DD-YYYY. Returned rows use normalized keys (x0020 stripped):
        REGISTRATION_NUMBER, NAME, BUSINESS_NAME, ADDRESS_1, ADDRESS_2,
        CITY, STATE, ZIP, REGISTRATION_DATE, TERMINATION_DATE.
        """
        return self._get("/Registrants/json/New", {"from": from_date, "to": to_date})

    # ----- endpoints: RegDocs -----

    def reg_docs(
        self,
        registration_number: int | str,
        doc_type: str | None = None,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """PDF filings for one registrant.

        Fields: DATE_STAMPED, REGISTRATION_NUMBER, REGISTRANT_NAME, DOCUMENT_TYPE,
        URL (direct PDF link at efile.fara.gov/docs/...), FOREIGN_PRINCIPAL_NAME,
        FOREIGN_PRINCIPAL_COUNTRY, SHORT_FORM_NAME.

        Optional filters:
          doc_type      one token from list_document_types() (e.g. 'AMENDMENT')
          country_code  2-letter FARA code from list_countries() (e.g. 'VE')
        """
        params: dict[str, str] = {}
        if doc_type:
            params["docType"] = doc_type
        if country_code:
            params["countryCode"] = country_code
        return self._get(f"/RegDocs/json/{registration_number}", params or None)

    # ----- endpoints: ShortFormRegistrants -----

    def short_form_active(self, registration_number: int | str) -> list[dict[str, Any]]:
        """Active short-form registrants (individuals filing under a registrant).

        Fields: REG_NUMBER, REGISTRANT_NAME, SF_FIRST_NAME, SF_LAST_NAME,
        ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP, REG_DATE, SHORTFORM_DATE.
        """
        return self._get(f"/ShortFormRegistrants/json/Active/{registration_number}")

    def short_form_terminated(self, registration_number: int | str) -> list[dict[str, Any]]:
        """Terminated short-form registrants. Same fields as short_form_active plus SF_TERM_DATE."""
        return self._get(f"/ShortFormRegistrants/json/Terminated/{registration_number}")

    # ----- endpoints: ForeignPrincipals -----

    def foreign_principals_active(self, registration_number: int | str) -> list[dict[str, Any]]:
        """Active foreign principals for one registrant.

        Fields: REG_NUMBER, REGISTRANT_NAME, FP_NAME, COUNTRY_NAME (full name, not code),
        ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP, REG_DATE, FP_REG_DATE.
        """
        return self._get(f"/ForeignPrincipals/json/Active/{registration_number}")

    def foreign_principals_terminated(self, registration_number: int | str) -> list[dict[str, Any]]:
        """Terminated foreign principals. Same fields as the active variant."""
        return self._get(f"/ForeignPrincipals/json/Terminated/{registration_number}")

    # ----- supporting lookup endpoints (undocumented in the public doc page) -----

    def list_countries(self) -> list[dict[str, Any]]:
        """FARA country codes. Rows: {COUNTRY_NAME, COUNTRY_CD}. Used for RegDocs countryCode filter."""
        return self._get("/Countries/json")

    def list_document_types(self) -> list[dict[str, Any]]:
        """FARA document type tokens. Rows: {Document_Type}. Used for RegDocs docType filter."""
        return self._get("/DocumentTypes/json")

    # ----- bulk CSV downloads (a separate, non-rate-limited data path) -----
    #
    # The /bulk/ files live at https://efile.fara.gov/bulk/zip/, are refreshed
    # daily, and contain the FULL dataset (active + terminated) — one CSV for
    # each domain. These are the right tool for country-level or cross-registrant
    # queries; answering "who's registered for Venezuela?" from the API would
    # require iterating 560 registrants at 5 req / 10 s (~20 min), but the bulk
    # FP CSV answers it in one download.
    #
    # Column names include literal spaces — the client normalizes to
    # snake_case_upper to match the rest of the API's shape.

    _BULK_FILES = {
        "registrants": "FARA_All_Registrants.csv.zip",
        "registrant_docs": "FARA_All_RegistrantDocs.csv.zip",
        "short_forms": "FARA_All_ShortForms.csv.zip",
        "foreign_principals": "FARA_All_ForeignPrincipals.csv.zip",
    }

    def _bulk_csv_rows(self, key: str, cache_dir: str | None = None, max_age_s: int = 3600) -> list[dict[str, str]]:
        """Download, cache, unzip, and parse one of the bulk CSV dumps.

        Default cache location is `$TMPDIR/fara_bulk/`, valid for 1 hour.
        Pass `cache_dir=None` and `max_age_s=0` to force a fresh download.
        """
        fname = self._BULK_FILES[key]
        cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "fara_bulk")
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, fname)

        fresh_enough = (
            max_age_s > 0
            and os.path.exists(cache_path)
            and (time.time() - os.path.getmtime(cache_path)) < max_age_s
        )
        if not fresh_enough:
            # Route through _request so bulk downloads get the same
            # retry-with-backoff + rate-limiting as the JSON API.
            url = f"{BULK_URL}/{fname}"
            data, status = self._request(url)
            if status >= 400:
                raise FaraApiError(f"Bulk download HTTP {status} from {url}")
            with open(cache_path, "wb") as f:
                f.write(data)

        with zipfile.ZipFile(cache_path) as zf:
            inner = [n for n in zf.namelist() if n.endswith(".csv")][0]
            with zf.open(inner) as f:
                text = f.read().decode("iso-8859-1", errors="replace")

        reader = csv.DictReader(io.StringIO(text))
        out = []
        for row in reader:
            normalized = {}
            for k, v in row.items():
                if k is None:
                    # DictReader puts extra columns under the None key as a list
                    continue
                key = k.strip().upper().replace(" ", "_").replace("/", "_")
                normalized[key] = v.strip() if isinstance(v, str) else ("" if v is None else v)
            out.append(normalized)
        return out

    def bulk_foreign_principals(self, **kw) -> list[dict[str, str]]:
        """All foreign principals (active + terminated) in one download.

        Columns (normalized):
        FOREIGN_PRINCIPAL_TERMINATION_DATE, FOREIGN_PRINCIPAL,
        FOREIGN_PRINCIPAL_REGISTRATION_DATE, COUNTRY_LOCATION_REPRESENTED,
        REGISTRATION_NUMBER, REGISTRANT_DATE, REGISTRANT_NAME,
        ADDRESS_1, ADDRESS_2, CITY, STATE, ZIP.

        Active-only filter: `[r for r in rows if not r['FOREIGN_PRINCIPAL_TERMINATION_DATE']]`.
        """
        return self._bulk_csv_rows("foreign_principals", **kw)

    def bulk_registrants(self, **kw) -> list[dict[str, str]]:
        """All registrants (active + terminated) in one download."""
        return self._bulk_csv_rows("registrants", **kw)

    def bulk_registrant_docs(self, **kw) -> list[dict[str, str]]:
        """All PDF filings across every registrant in one download."""
        return self._bulk_csv_rows("registrant_docs", **kw)

    def bulk_short_forms(self, **kw) -> list[dict[str, str]]:
        """All short-form registrants (active + terminated) in one download."""
        return self._bulk_csv_rows("short_forms", **kw)

    # ----- convenience helpers -----

    def profile(self, registration_number: int | str) -> dict[str, Any]:
        """Everything about one registrant in a single dict. Swallows FaraApiError per sub-call."""
        reg = str(registration_number)

        def _safe(fn, *a, **kw):
            try:
                return fn(*a, **kw)
            except FaraApiError:
                return []

        return {
            "registration_number": int(reg) if reg.isdigit() else reg,
            "foreign_principals_active": _safe(self.foreign_principals_active, reg),
            "foreign_principals_terminated": _safe(self.foreign_principals_terminated, reg),
            "short_form_active": _safe(self.short_form_active, reg),
            "short_form_terminated": _safe(self.short_form_terminated, reg),
            "reg_docs": _safe(self.reg_docs, reg),
        }

    def iter_all_foreign_principals(
        self, include_terminated: bool = False
    ) -> Iterable[dict[str, Any]]:
        """Yield every foreign principal by iterating all registrants.

        Expensive: ~560 requests for active-only (~2 minutes at 5 req / 10 s).
        Include terminated and you're iterating ~7,000+ registrants (6+ hours).
        """
        for reg in self.list_active():
            reg_num = reg["Registration_Number"]
            try:
                fps = self.foreign_principals_active(reg_num)
            except FaraApiError:
                fps = []
            for fp in fps:
                yield {**fp, "_status": "active"}
        if include_terminated:
            for reg in self.list_terminated():
                reg_num = reg["Registration_Number"]
                try:
                    fps = self.foreign_principals_terminated(reg_num)
                except FaraApiError:
                    fps = []
                for fp in fps:
                    yield {**fp, "_status": "terminated"}


# --------- CLI ---------


def _print_json(obj: Any) -> None:
    json.dump(obj, sys.stdout, indent=2, default=str, ensure_ascii=False)
    sys.stdout.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FARA eFile API client")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-active", help="All active registrants")
    sub.add_parser("list-terminated", help="All terminated registrants")
    sub.add_parser("list-countries", help="Lookup: country codes (COUNTRY_NAME + COUNTRY_CD)")
    sub.add_parser("list-doc-types", help="Lookup: document type tokens for --doc-type")

    n = sub.add_parser("list-new", help="Registrants with Registration_Date in window")
    n.add_argument("--from", dest="from_date", required=True, help="MM-DD-YYYY")
    n.add_argument("--to", dest="to_date", required=True, help="MM-DD-YYYY")

    r = sub.add_parser("regdocs", help="PDF filings for a registrant")
    r.add_argument("registration_number")
    r.add_argument("--doc-type", help="e.g. AMENDMENT, EXHIBIT_AB, REGISTRATION_STATEMENT")
    r.add_argument("--country-code", help="2-letter FARA code, e.g. VE, AF")

    for cmd, help_ in [
        ("sf-active", "Active short-form registrants for a registrant"),
        ("sf-terminated", "Terminated short-form registrants"),
        ("fp-active", "Active foreign principals"),
        ("fp-terminated", "Terminated foreign principals"),
        ("profile", "Everything about one registrant (FPs + SFs + filings)"),
    ]:
        s = sub.add_parser(cmd, help=help_)
        s.add_argument("registration_number")

    for cmd, help_ in [
        ("bulk-foreign-principals", "Download bulk FP CSV (active+terminated, daily refresh)"),
        ("bulk-registrants", "Download bulk registrants CSV"),
        ("bulk-registrant-docs", "Download bulk registrant-docs CSV (every filing)"),
        ("bulk-short-forms", "Download bulk short-forms CSV"),
    ]:
        s = sub.add_parser(cmd, help=help_)
        s.add_argument("--country", help="filter by COUNTRY_LOCATION_REPRESENTED substring (case-insensitive)")
        s.add_argument("--active-only", action="store_true",
                       help="drop rows with any non-empty *_TERMINATION_DATE")
        s.add_argument("--force-refresh", action="store_true", help="bypass 1-hour cache")

    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    c = FaraClient()
    try:
        if args.cmd == "list-active":
            _print_json(c.list_active())
        elif args.cmd == "list-terminated":
            _print_json(c.list_terminated())
        elif args.cmd == "list-countries":
            _print_json(c.list_countries())
        elif args.cmd == "list-doc-types":
            _print_json(c.list_document_types())
        elif args.cmd == "list-new":
            _print_json(c.list_new(args.from_date, args.to_date))
        elif args.cmd == "regdocs":
            _print_json(c.reg_docs(args.registration_number, args.doc_type, args.country_code))
        elif args.cmd == "sf-active":
            _print_json(c.short_form_active(args.registration_number))
        elif args.cmd == "sf-terminated":
            _print_json(c.short_form_terminated(args.registration_number))
        elif args.cmd == "fp-active":
            _print_json(c.foreign_principals_active(args.registration_number))
        elif args.cmd == "fp-terminated":
            _print_json(c.foreign_principals_terminated(args.registration_number))
        elif args.cmd == "profile":
            _print_json(c.profile(args.registration_number))
        elif args.cmd.startswith("bulk-"):
            key = args.cmd.removeprefix("bulk-").replace("-", "_")
            kw = {"max_age_s": 0} if args.force_refresh else {}
            rows = getattr(c, f"bulk_{key}")(**kw)
            if args.active_only:
                term_cols = [k for k in rows[0] if "TERMINATION_DATE" in k] if rows else []
                rows = [r for r in rows if all(not r.get(c) for c in term_cols)]
            if args.country:
                needle = args.country.lower()
                country_cols = [k for k in rows[0] if "COUNTRY" in k] if rows else []
                rows = [r for r in rows if any(needle in r.get(c, "").lower() for c in country_cols)]
            _print_json(rows)
    except FaraApiError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
