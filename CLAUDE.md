# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of small, **self-contained** code snippets. Each snippet lives in its own
top-level folder (e.g. `google_news_url/`) and is independent — there is no shared
library, build system, package manifest, or test suite at the repo root. The root
`README.md` is an index table; every snippet folder has its own `README.md` describing
what it does and how to run it.

## Conventions when adding or editing snippets

- **One folder per snippet.** Keep everything a snippet needs inside its folder. Do not
  introduce cross-snippet imports or a shared root package.
- **Each snippet folder gets its own `README.md`**, and the new snippet must be added as a
  row to the table in the root `README.md`.
- **Parallel implementations stay equivalent.** Some snippets ship the same logic in
  multiple runtimes (e.g. `google_new_url.py` and `google_new_url.mjs`). When you change
  the behavior of one, mirror it in the other so they produce identical output.
- **Python snippets use `uv` with inline PEP 723 dependencies** declared in a
  `# /// script` header — no `requirements.txt` or virtualenv setup. They run with
  `uv run <file>.py`, which installs declared deps automatically.
- **Node snippets target Node 18+** and prefer built-ins (`fetch`, `AbortSignal.timeout`)
  with no external packages / no `package.json`.
- Scripts take their input as `argv[1]` and fall back to a hard-coded default URL/value so
  they can be run with no arguments for a quick smoke test.

## Demo pages (GitLab / GitHub Pages)

The repo root is also published as a static site: `.gitlab-ci.yml` copies the HTML,
`favicon.svg`, `robots.txt` and each demo folder into `public/`, while
`.github/workflows/deploy.yml` uploads the whole tree — both on push to `main`/`master`.
Navigation is two levels of list page: root `index.html` links to one
`<snippet>/index.html` per snippet folder, and that folder list links to one page per
demo, **named after the script it ports** (`open_meteo/open-meteo.html` ports
`open_meteo/open-meteo.py`); an alternate view of the same script adds a `_suffix`
(`open-meteo_readable.html`). List pages carry no logic — they are the same small card
markup, differing only in title and links.

**Adding a demo means: a `<snippet>/<script-name>.html` page, a link on that folder's
`index.html`, a row in the root `README.md` "Demo pages" table, and — if the snippet
folder is new to Pages — a link on the root `index.html` plus the folder added to the
`cp -r` line in `.gitlab-ci.yml`** (the GitHub workflow uploads the whole tree and needs
no change).

Pages hosting is static, so a demo page **cannot run the snippet's Python**. It is a
JavaScript re-implementation that calls the upstream API directly from the browser, which
makes it a parallel implementation under the rule above: change one, mirror the other.
This is only viable for keyless, CORS-enabled APIs. `cwa_opendata` needs an API key
(which would be readable in page source) and `google_news_url` scrapes cross-origin, so
neither can be demoed without a server — they are deliberately listed as todo in
`index.html` rather than half-implemented.

## Running

```bash
# Python (deps auto-installed from the PEP 723 header)
uv run google_news_url/google_new_url.py [arg]

# Node (no install step)
node google_news_url/google_new_url.mjs [arg]
```

There is no lint or test command; verify a snippet by running it.

## cwa_opendata specifics

Queries Taiwan CWA Open Data REST datastore endpoints
(`https://opendata.cwa.gov.tw/api/v1/rest/datastore/<dataset-id>`) with an API key
(`Authorization` query param), `CountyName`, and a `timeFrom`/`timeTo` date window.
The key comes from the `CWA_API_KEY` env var or root `config.yml` (gitignored; see
`config_example.yml`) — never hard-code credentials in snippets. `cwa_sunrise.py` uses dataset `A-B0062-001` (a 1-day
window); `cwa_moonrise.py` uses `A-B0063-001` with a 3-day window (yesterday/today/
tomorrow) because moon rise/transit/set can be missing on a given date or fall on an
adjacent day — `pick_moon_events()` stitches the cycle together, labeling borrowed
times with 昨/明. Note: the site's TLS certificate lacks a Subject Key Identifier, so
both scripts relax `ssl.VERIFY_X509_STRICT` (Python 3.13 default) via a custom
`HTTPAdapter` while keeping normal certificate verification.

## open_meteo specifics

`open-meteo.html` is the browser port of `open-meteo.py` (see "Demo pages"); `index.html`
is only this folder's list page. Form fields stand
in for the CLI arguments and it reproduces the script's URL construction exactly —
`encodeURIComponent` with `%2C` mapped back to a literal comma and `%20` to `+`, matching
`urlencode(params, safe=",")` byte for byte — so `get_para` stays the real request URL.
Like the script, it displays an API error body instead of throwing.

`open-meteo_readable.html` issues the same request (its request core is copied from
`open-meteo.html` verbatim — change one, change all three) and renders the response as an
hour-by-hour grid: a tab per model, a row per `hourly` variable, colour-graded cells, a
sticky label column and horizontal scroll. It is the page that has to cope with the
suffixing rule at runtime, so `seriesKey()` accepts both `<var>_<model>` and bare `<var>`.
Two API quirks it handles and that any similar page will hit: a model that does not
publish a variable still returns a key — nulls all the way down, with the unit reported as
the **literal string `"undefined"`** (so with the default four models, three of the
`visibility` tabs are a row of dashes) — and `forecast_days` starts the series at 00:00
local, so past hours are trimmed using `utc_offset_seconds` (the 從現在開始 checkbox).

Grid rows follow the order of the `hourly` parameter, so this page's `HOURLY_VARS` lists
the cloud decks high → mid → low while `open-meteo.py`/`.html` list them low → high. That
listing order is the **only** intended difference between the three; treat any other
divergence as a bug.

It also carries a JavaScript port of the Meeus solar/lunar series from `milkyway.py` (sun
and moon altitude, moon illumination) for the 太陽高度/月亮高度/月相 rows, which Open-Meteo
cannot supply — it offers only sunrise/sunset and `daily=moon_phase`. **This is a fourth
parallel implementation: it is verified to agree with `milkyway.py` to four decimal places,
so changing the astronomy in either means re-checking both.** `julianDay()` uses the Unix
epoch (JD 2440587.5) instead of the Python's Gregorian calendar arithmetic; the two are
exactly equivalent. Because these rows depend only on place and time they are identical on
every model tab, and the solar altitude — not an `is_day` series or an hour-of-day rule —
is what makes the 天氣 icons switch between sun and moon.

`open-meteo.py` is the bare API demo: it builds the request URL itself with
`urlencode(params, safe=",")` and requests that exact string, so the `get_para` key it
adds to the response is the real URL rather than a reconstruction (`requests` would
percent-encode the commas in the `hourly`/`models` lists). It returns API errors instead
of raising, prints request metadata to stderr so stdout stays pipeable JSON, and exits 1
on a non-2xx. Note the filename is hyphenated, so it is a script only — not importable.

`milkyway.py` scores each upcoming hour for Milky Way astrophotography at a `lat,lon`.
No API key — Open-Meteo's free tier is keyless (10,000 calls/day), so there is nothing to
read from `config.yml`. It queries `hourly=` cloud/moisture variables with
`&models=ecmwf_ifs025,gfs_global,jma_gsm,icon_global`, which suffixes every series with
its model name (`cloud_cover_gfs_global`) — and not every model publishes every variable
(of the four, **only gfs returns `visibility`**; `precipitation_probability` is null for
jma), so `_hour_vars()` fills gaps from the ensemble mean, which for `visibility` means
gfs on its own. Suffixing only happens with two or
more models; a single-model `MODELS` returns bare keys and would silently score every
hour as a perfect sky, so `fetch_forecast()` validates the response shape. `sky_quality()` is scored per model and
averaged; the spread across models plus forecast lead time drives the 信心 column, which
is intentionally a separate axis from the score. Astronomy (sun altitude, moon
altitude/illumination, galactic core altitude) is computed locally with Meeus
low-precision series rather than fetched — Open-Meteo offers only sunrise/sunset and
`daily=moon_phase`. Because `forecast_days` starts the series at 00:00 local, `score_hours()`
drops hours before the current one. When tuning the formula, sanity-check both ends:
Taiwan in monsoon season should score near zero, and a pristine site (e.g. Atacama
`-24.6,-70.4`) should reach ~100%.

## google_news_url specifics

Resolves a Google News redirect link (from the search RSS feed) to the real article URL by
mimicking the browser: (1) `GET` the article page to scrape the `data-n-a-sg` (signature),
`data-n-a-ts` (timestamp), and `data-n-a-id` attributes, then (2) `POST` those to the
`batchexecute` RPC (`rpcids=Fbv4je`) and parse the real URL out of the `wrb.fr` row. This
depends on Google's page structure and RPC payload shape — if Google changes either, the
attribute scraping or response parsing is what breaks.
