# US CS Conference Finder

Windows desktop app that discovers upcoming **US** computer-science conferences by topic, ranks them by **CORE/CCF** prestige, and shows links to submit papers and attend.

## Features

- Topic dropdown (CCF-style CS subfields) mapped to WikiCFP categories
- Semantic search bar (local TF-IDF, no API key)
- Filters: US locations only, excludes past conferences
- Results sorted by prestige (CORE A\*/A/B/C + CCF bonus + h5-index)
- Double-click **Submit** or **Attend** to open links in your browser
- Live web discovery: WikiCFP + Google/DuckDuckGo web search on each session's first Search
- Session in-memory cache (cleared when the app exits; repeat Search in same session is instant)

## Requirements

- Python 3.10+
- Windows (for `.exe`; app runs cross-platform in dev)

## Setup

```powershell
cd Time_table
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Run (development)

Use the project virtual environment (system `python` often lacks dependencies):

```powershell
.\run.ps1
```

Or manually:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src\main.py
```

Do **not** use bare `python src/main.py` unless that interpreter already has `requirements.txt` installed.

## Build executable

`pyinstaller` is only in the project `.venv`, not on global PATH.

```powershell
.\build.ps1
```

Or manually:

```powershell
.\.venv\Scripts\pyinstaller.exe build.spec --noconfirm
```

Close `ConferenceFinder.exe` before rebuilding if you see “Access is denied”.

Output: `dist/ConferenceFinder.exe`

## Project layout

```
src/
  main.py              Entry point
  ui/                  Tkinter UI
  discovery/           WikiCFP + developers.events
  filters/             US location, upcoming dates
  ranking/             CORE/CCF matching, prestige sort, links
  search/              Topics, semantic search, orchestrator
  storage/             Session in-memory cache (+ optional SQLite fallback)
  data/                Bundled rankings (core_rankings.csv, ccf_deadlines/)
tests/                 Unit tests with HTML fixtures
```

## Data sources

- [WikiCFP](http://www.wikicfp.com) — conference discovery (live scrape)
- Google/DuckDuckGo web search — supplemental discovery via `ddgs` (optional `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_ID` for official Custom Search)
- Bundled [CORE](https://portal.core.edu.au/conf-ranks/)-style rankings CSV
- Bundled [CCF-Deadlines](https://github.com/ccfddl/ccf-deadlines)-style YAML subset
- Optional: [developers.events](https://developers.events) CFP JSON for extra links

## Tests

```powershell
python -m pytest tests/ -v
```

## Related work

See project plan for GitHub, Stack Overflow, and Google Scholar references (Agentic_Conference_Crawler, ccf-deadlines, wikicfp-scanner, GraphConfRec, Where to Submit).

## Limitations

- Prestige matching depends on acronym/title fuzzy match to bundled rankings
- WikiCFP HTML layout may change; parser has fixture tests
- Not a crawl of the entire web — WikiCFP + web search + curated rankings + optional developers.events
- First Search each app session requires internet; identical repeat searches use session cache until you close the app
