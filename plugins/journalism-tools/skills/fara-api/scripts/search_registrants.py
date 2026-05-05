#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Find registrants by name substring, with punctuation-insensitive matching.

FARA has no server-side name search. This pulls the bulk Active (+ optionally
Terminated) lists — 1 or 2 API calls total — and filters locally.

Why punctuation normalization: many firms are stored with commas / ampersands
that break naive substring matching. "Akin Gump" doesn't match the stored
"Akin, Gump, Strauss, Hauer & Feld, LLP" under plain `in`. We strip punctuation
and collapse whitespace before comparing, so a query of "akin gump" hits.

All matches are returned. When multiple records match one query, the output
clearly flags ambiguity rather than silently picking one.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fara_client import FaraClient, FaraApiError  # noqa: E402


_PUNCT = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")


def _normalize(s: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace."""
    return _SPACES.sub(" ", _PUNCT.sub(" ", s.lower())).strip()


def _score(needle_norm: str, name_norm: str) -> float:
    """Rough rank: exact token-sequence match beats partial, word-boundary beats infix."""
    if needle_norm == name_norm:
        return 3.0
    if re.search(rf"\b{re.escape(needle_norm)}\b", name_norm):
        return 2.0
    if needle_norm in name_norm:
        return 1.0
    return 0.0


def search(client: FaraClient, needle: str, active_only: bool = False) -> list[dict]:
    needle_norm = _normalize(needle)
    if not needle_norm:
        return []

    hits: list[dict] = []
    try:
        for r in client.list_active():
            sc = _score(needle_norm, _normalize(r["Name"]))
            if sc:
                hits.append({**r, "_status": "active", "_match_score": sc})
        if not active_only:
            for r in client.list_terminated():
                sc = _score(needle_norm, _normalize(r["Name"]))
                if sc:
                    hits.append({**r, "_status": "terminated", "_match_score": sc})
    except FaraApiError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    # Sort: active first, then by match score, then by Registration_Number desc (newer first)
    hits.sort(key=lambda h: (h["_status"] != "active", -h["_match_score"], -h["Registration_Number"]))
    return hits


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("needle", help="substring to match against Name (punctuation- and case-insensitive)")
    p.add_argument("--active-only", action="store_true", help="skip the Terminated list")
    p.add_argument("--best-match", action="store_true",
                   help="emit only the single best match; exits 1 with a warning if ambiguous "
                        "(multiple high-scoring active matches or only terminated matches)")
    args = p.parse_args(argv)

    hits = search(FaraClient(), args.needle, active_only=args.active_only)

    if args.best_match:
        active = [h for h in hits if h["_status"] == "active"]
        top_active = [h for h in active if h["_match_score"] == active[0]["_match_score"]] if active else []

        if len(top_active) == 1:
            json.dump(top_active[0], sys.stdout, indent=2, default=str, ensure_ascii=False)
            sys.stdout.write("\n")
            return
        if len(top_active) > 1:
            print(
                f"warning: ambiguous — {len(top_active)} active registrants tied for top match. "
                f"Candidates: {[h['Name'] for h in top_active]}",
                file=sys.stderr,
            )
            json.dump(top_active, sys.stdout, indent=2, default=str, ensure_ascii=False)
            sys.stdout.write("\n")
            sys.exit(1)
        if hits:
            print(
                f"warning: no active match; {len(hits)} terminated candidate(s). "
                f"Top: {hits[0]['Name']} (reg {hits[0]['Registration_Number']}, "
                f"terminated {hits[0].get('Termination_Date', '?')})",
                file=sys.stderr,
            )
            json.dump(hits[0], sys.stdout, indent=2, default=str, ensure_ascii=False)
            sys.stdout.write("\n")
            sys.exit(1)
        print(f"no match found for {args.needle!r}", file=sys.stderr)
        sys.exit(1)

    json.dump(hits, sys.stdout, indent=2, default=str, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
