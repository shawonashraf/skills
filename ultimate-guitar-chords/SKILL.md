---
name: ultimate-guitar-chords
description: Find and fetch song chords from ultimate-guitar.com.
version: 0.1.0
author: Shawon Ashraf, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [music, chords, guitar, scraping]
    related_skills: []
---

# Ultimate Guitar Chords Skill

Given a song title (and optionally an artist), find the chord tab on
ultimate-guitar.com and print clean chords. Works without a browser: UG
server-renders its full page state into a `<div class="js-store"
data-content="...">` JSON blob, which `scripts/ug_chords.py` (stdlib-only
urllib) parses directly. Paywalled Official/Pro tabs are skipped
automatically; free community tabs are used.

## When to Use

- User asks for chords / tab / "how to play" for a named song.
- User asks for the key, tuning, or difficulty of a song as tablature.
- Don't use for: strumming patterns audio, sheet music (PDF), or lyrics-only
  requests.

## Prerequisites

Python 3.10+ with stdlib only (urllib, json, re, html, argparse). No installs,
no API key, no browser. Network access to ultimate-guitar.com.

## How to Run

From this skill's directory, via the `terminal` tool:

```
python3 scripts/ug_chords.py search "<song title>" [artist-filter]
python3 scripts/ug_chords.py fetch <tab-url>
```

## Procedure

1. **Search with the SONG TITLE ONLY**:
   `terminal(command="python3 scripts/ug_chords.py search \"Hotel California\"", timeout=60)`.
   The artist is an optional second positional arg used only to FILTER rows —
   putting the artist inside the query string returns "No results".
   Output rows are sorted by votes/rating; completion criterion: at least one
   row printed as `votes=… rating=… Artist — Song <tab_url>`.
2. **Pick the tab**: take the first row whose `type` is chords (the script
   already filters to Chords / Ukulele Chords and drops Pro promo rows). If
   the user named an artist, pass it as the filter arg. If the user asked for
   ukulele, keep the `ukulele` URL.
3. **Fetch chords**:
   `terminal(command="python3 scripts/ug_chords.py fetch <tab_url>", timeout=60)`.
   Output starts with meta (title, artist, Difficulty, Key, Level, Tuning)
   then the tab body with chords aligned over lyrics. Completion criterion:
   non-empty chord body.
4. **Deliver**: paste the chord body in a fenced block (alignment is
   monospaced — fences are mandatory), plus the Source URL and key/tuning.

## Quick Reference

| Goal                             | Command                                              |
|----------------------------------|------------------------------------------------------|
| List candidate tabs              | `search "song title" [artist]`                       |
| Print chords for a tab URL       | `fetch https://tabs.ultimate-guitar.com/tab/…-<id>`  |
| Wrong/no results                 | retry with a different song-title spelling, no artist in query |

## Pitfalls

- **Artist in the query breaks search.** `search "wonderwall oasis"` →
  no results. Use `search "wonderwall" oasis` (artist is the filter arg).
- **Official/Pro tabs are paywalled** — their content is empty; `fetch` exits
  with a message. Pick a high-vote community tab from `search` output instead
  (the search rows already exclude promo rows without a free `tab_url`, but a
  tab page can still be empty; then fall back to the next row).
- **`js-store` blob missing** → UG changed layout or blocked the request. Fall
  back to the `browser_exec` tool: open the tab URL and read the tab body from
  the DOM.
- **Variations/live versions**: search returns every version; if the user
  wants a specific album/live arrangement, disambiguate from the song_name
  field before fetching.
- Chord-over-lyric alignment is whitespace-sensitive — never reflow the body
  when pasting.

## Verification

- `search` prints at least one `votes=… <tab_url>` row for the song.
- `fetch` prints a `Source:` line followed by a non-empty body containing
  real chord symbols (e.g. `Em7`, `Dsus4`).
- Known-good canary: `search "Wonderwall" "Oasis"` returns
  `…/oasis/wonderwall-chords-39144` (12k+ votes) and `fetch` of it prints
  key F#m and the Em7/G/Dsus4/A7sus4 progression.
