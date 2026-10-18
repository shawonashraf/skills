#!/usr/bin/env python3
"""Fetch chords from ultimate-guitar.com without a browser (stdlib only).

UG server-renders its full page state into
<div class="js-store" data-content="..."> as an HTML-escaped JSON blob:
  - search page : store.page.data.results[] + store.page.data.pagination
  - tab page    : store.page.data.tab_view.wiki_tab.content (UG BBCode)
so plain urllib gets everything a browser would show for free tabs.

Usage:
  ug_chords.py search "<song title>" [artist-filter]   # list matching tabs
  ug_chords.py fetch <tab-url>                          # print clean chords

Notes:
  - Query search with the SONG TITLE only; adding the artist to the query
    returns "No results". Filter by artist afterwards (2nd arg).
  - results[] mixes Pro/official promo rows (no free tab_url) with real
    community tabs; this script keeps only the latter.
  - Official/Pro tabs are paywalled (wiki_tab.content empty). Free
    community tabs have full content; search ranks them by votes/rating.
"""
import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:130.0) "
      "Gecko/20100101 Firefox/130.0")

# UG tab markup tags stripped while keeping their inner text.
_TAG = re.compile(
    r"\[/(?:tab|comment2?|highlight|section|open|b|i|u|keymaster|brush|"
    r"accidental)\]|\["
    r"(?:tab|comment2?|highlight|section|b|i|u|keymaster|brush|accidental)\]"
    r"|\[ch\]|\[/ch\]|\[open[^\]]*\]|\[rating\][^\[]*\[/rating\]"
)


def get_store(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        page = resp.read().decode("utf-8", errors="replace")
    m = re.search(r'class="js-store" data-content="([^"]+)"', page)
    if not m:
        raise SystemExit(
            "no js-store blob found — page layout changed or request blocked")
    return json.loads(html.unescape(m.group(1)))["store"]["page"]["data"]


def clean_content(raw: str) -> str:
    # [ch]C[/ch] keeps the chord letter in place (preserves alignment of
    # chords over lyrics); foldable [open]...[/open] sections keep content.
    text = _TAG.sub("", raw)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{4,}", "\n\n\n", text).strip()


def cmd_search(query: str, artist: str | None) -> None:
    base = ("https://www.ultimate-guitar.com/search.php?"
            "search_type=title&value=" + urllib.parse.quote(query))
    rows, page_no, total_pages = [], 1, 1
    while page_no <= total_pages:
        data = get_store(base + (f"&page={page_no}" if page_no > 1 else ""))
        if page_no == 1:
            if not data.get("results"):
                sys.exit("no results — search with the song title only "
                         "(no artist)")
            total_pages = min((data.get("pagination") or {}).get("total", 1), 3)
        for t in data.get("results", []):
            if not t.get("type"):           # Pro/official promo row
                continue
            if t.get("type") not in ("Chords", "Ukulele Chords"):
                continue
            if artist and artist.lower() not in t.get("artist_name", "").lower():
                continue
            rows.append(t)
        page_no += 1
    if not rows:
        sys.exit("no free chords-type tab matched — try without the artist "
                 "filter, or a different spelling of the song title")
    rows.sort(key=lambda t: (-(t.get("votes") or 0), -(t.get("rating") or 0)))
    for t in rows[:10]:
        print(f"votes={t.get('votes', 0):>6}  rating={t.get('rating', 0):.2f}  "
              f"{t['artist_name']} — {t['song_name']}  {t['tab_url']}")


def cmd_fetch(url: str) -> None:
    data = get_store(url)
    tab = data.get("tab") or {}
    meta = []
    if tab.get("song_name"):
        meta.append(f"{tab['song_name']} — {tab.get('artist_name', '?')}")
    for key, label in (("difficulty", "Difficulty"),
                       ("tonality_name", "Key"),
                       ("ug_difficulty", "Level")):
        if tab.get(key):
            meta.append(f"{label}: {tab[key]}")
    try:
        tuning = tab["adapted"]["tuning"]["current"]
        if tuning:
            meta.append(f"Tuning: {tuning}")
    except (KeyError, TypeError):
        pass
    content = ((data.get("tab_view") or {}).get("wiki_tab") or {}).get("content", "")
    if not content.strip():
        sys.exit("this tab has no free content (Official/Pro paywalled) — "
                 "run 'search' and pick a high-vote community version")
    if meta:
        print("\n".join(meta))
    print(f"Source: {url}\n")
    print(clean_content(content))


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch chords from ultimate-guitar.com")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query", help="song title only")
    s.add_argument("artist", nargs="?", help="optional artist filter")
    f = sub.add_parser("fetch")
    f.add_argument("url")
    a = p.parse_args()
    if a.cmd == "search":
        cmd_search(a.query, a.artist)
    else:
        cmd_fetch(a.url)


if __name__ == "__main__":
    main()
