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
This is effortless for keyless, CORS-enabled APIs (Open-Meteo). `cwa_opendata` needs an
API key, which would be readable in page source, so it has no demo and is deliberately
listed as todo in `index.html` rather than half-implemented. `google_news_url` is
cross-origin with no CORS headers at all and gets around it with a **user-selected public
CORS proxy** — see below; that is the only reason it has a page.

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

`open-meteo.html` is the browser port of `open-meteo.py` (see "Demo pages"), listed as
**open-meteo API** on `index.html`, which is only this folder's list page. Form fields stand
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

`DEFAULT_EXTRA` prefills two lines into the extra-params box — kept there, not in
`defaultParams()`, so the request core stays identical to the script:

- `daily=sunrise,sunset,moon_phase`. **Model suffixing applies to `daily` as well as
  `hourly`**, so four models return twelve daily series; they are pure astronomy, so every
  model's `moon_phase` is byte-identical and sunrise/sunset differ only by grid-point
  rounding. The readable grid renders `hourly` only, so this surfaces in the raw JSON panel
  alone — it is a cross-check, never a data source: the 太陽/月亮/月相 rows come from the
  page's own Meeus port, so clearing the line changes nothing on screen. The extra-params
  hint says so, on both pages.
- `past_days=7`, which takes the response from ~33 KB / 168 hours to ~64 KB / 336 hours
  (billing counts time range, not just variables). The API accepts `past_days` up to **93**,
  but the models keep only a rolling ~2-month archive (the JMA models shortest,
  `ecmwf_ifs025` longest), so **~61 is the practical maximum** — beyond it the extra hours are nulls. At 61
  the response is ~300 KB / 1632 hours and the 從現在開始 trim is what keeps the grid usable:
  unticked that is 68 day groups, ~24,500 cells. Anything iterating the whole series should
  assume that scale is reachable from the form.

**The two pages share their whole form**, so switching between raw JSON and the grid needs
no retyping — `PLACES`, `DEFAULT_LAT`/`DEFAULT_LON`, `HOURLY_VARS`, `MODELS`,
`DEFAULT_EXTRA`, the `.locrow`/`.place` CSS and `buildPlaces()`/`markActivePlace()` are
duplicated verbatim in both. **Edit one and you must edit the other**; there is no shared
file, by the one-folder-per-snippet rule. `milkyway_readable.html` is a third copy of
`PLACES`, the saved-spot CSS and `buildPlaces()`/`markActivePlace()` — but *not* of
`HOURLY_VARS`/`MODELS`/`DEFAULT_EXTRA`, which it deliberately overrides.

All three pages also carry a verbatim copy of `reverseGeocode()`/`appendPlaceName()`,
which puts `countryName/principalSubdivision/city/locality` (e.g.
中華民國/宜蘭縣/南澳鄉/蘇澳鎮) on a **second meta line** from BigDataCloud's keyless,
CORS-enabled `reverse-geocode-client`. The break is a `<br>` node appended to the
element, not a `\n` in the text — `.meta` wraps normally, so a newline would render
as a space. It is sent the **requested** lat/lon, not the
response's grid point — the two can name different townships. The lookup is fired
after the result renders and never awaited, so it re-checks the meta text before
appending and skips it if a newer fetch has replaced the line; any failure resolves
to an empty string and leaves the line alone. It is a label, never data: nothing on
screen depends on it, and `open-meteo.py` has no equivalent, so this is the one place
`open-meteo.html`'s meta line deliberately says more than the script's stderr summary.

Three of those defaults intentionally differ from `open-meteo.py`. The request *machinery*
(`buildUrl`, `fetchForecast`, `paramsFromForm`) is still a byte-for-byte port, and any
divergence there is a bug:

- `HOURLY_VARS` lists the cloud decks high → mid → low, because grid rows follow the order
  of the `hourly` parameter; the script lists them low → high.
- `DEFAULT_LAT`/`DEFAULT_LON` come from `PLACES[0]` (the saved stargazing spots), not from
  the Taipei coordinates the script defaults to.
- `DEFAULT_EXTRA` adds `daily=...`, which the script does not send.

The location field sits **last in the form, directly above Fetch**, out of normal
parameter order on purpose: it is the only field a user changes, so it belongs next to the
button rather than at the top above five fields nobody edits. Keep it there.

`PLACES` drives both the default location and the buttons beside the location box; adding a
spot is one row there and nothing else, and reordering it changes what the pages open on.
Clicking a button fills the box **and refetches** — leaving a stale result under a new
location would misrepresent it. The buttons only reflect the box, so a hand-typed
coordinate leaves all of them unpressed. Note a click while a fetch is in flight is a
silent no-op: `requestSubmit()` does nothing while the submit button is disabled.

Row labels are deliberately terse (`LABELS`, `API_SHORT`, `UNIT_SHORT`): the label column
is `position: sticky`, so its width is subtracted from every scroll position — abbreviating
took it from 184px to 103px and bought two more hours on screen, which matters most on a
phone. The full API name lives on the `title` attribute, and an unlisted variable falls
back to its own (long, but never wrong) name. Keep new labels to two or three CJK
characters.

It also carries a JavaScript port of the Meeus solar/lunar series from `milkyway.py` (sun
and moon altitude, moon illumination) for the 太陽/月亮/月相 rows, which Open-Meteo
cannot supply — it offers only sunrise/sunset and `daily=moon_phase`. **This is a fourth
parallel implementation: it is verified to agree with `milkyway.py` to four decimal places,
so changing the astronomy in either means re-checking both.** `julianDay()` uses the Unix
epoch (JD 2440587.5) instead of the Python's Gregorian calendar arithmetic; the two are
exactly equivalent. Because these rows depend only on place and time they are identical on
every model tab, and the solar altitude — not an `is_day` series or an hour-of-day rule —
is what makes the 天氣 icons switch between sun and moon.

`milkyway_readable.html` is that grid stripped to what stargazing needs, and so is a
**fourth copy of the request core and a third copy of the Meeus astronomy** — the same
edit-one-edit-all rule applies to both. It fixes `hourly` (the four cloud decks only),
`models` (`icon_global` alone) and drops `DEFAULT_EXTRA` entirely, removing those three
textareas from the form; only `forecast_days`, `timezone` and the location remain. One
model means no tabs and **bare series keys**, which `seriesKey()` already resolves, and the
response drops to ~5.7 KB / 168 hours from ~64 KB / 336. The 銀河 row goes between 時間
and 天氣, green label, tinted `[0, 100, false]` so 100 is green. Its score is
`(100 − 雲量) × (100 − moonPenalty) / 100`, zeroed outright when the sun is above −10°,
where `moonPenalty` ramps 0→100 as moon altitude goes 0°→10° (`MOON_KILL_ALT`) and is 0
below the horizon — altitude only, so 月相 is left on screen to judge illumination by eye.
The moon used to be a hard `> 0° → 0` cutoff; the ramp exists because that threw away the
best hour of nights when a low moon was setting, so **don't "simplify" it back**. The score
is **deliberately not** a port of `sky_quality()` — a rule of thumb the user is still
revising, so the two are free to disagree. The astronomy underneath it is the shared part,
and is not.

`open-meteo.py` is the bare API demo: it builds the request URL itself with
`urlencode(params, safe=",")` and requests that exact string, so the `get_para` key it
adds to the response is the real URL rather than a reconstruction (`requests` would
percent-encode the commas in the `hourly`/`models` lists). It returns API errors instead
of raising, prints request metadata to stderr so stdout stays pipeable JSON, and exits 1
on a non-2xx. Note the filename is hyphenated, so it is a script only — not importable.

`milkyway.py` scores each upcoming hour for Milky Way astrophotography at a `lat,lon`.
No API key — Open-Meteo's free tier is keyless (10,000 calls/day), so there is nothing to
read from `config.yml`. It queries `hourly=` cloud/moisture variables with
`&models=icon_global,jma_seamless,gfs_global,ecmwf_ifs025`, which suffixes every series with
its model name (`cloud_cover_gfs_global`) — and not every model publishes every variable
(of the four, **only gfs returns `visibility`**; `precipitation_probability` is null for
jma), so `_hour_vars()` fills gaps from the ensemble mean, which for `visibility` means
gfs on its own. The model list is shared by `open-meteo.py` and both `open-meteo*.html`
pages (**not** `milkyway_readable.html`, which fixes `icon_global` alone), and its order is
the order rows/tabs appear in, so keep the four in step. `jma_seamless` rather than
`jma_msm` is deliberate: MSM is 0.05° ≈ 5 km over Taiwan but its domain stops near
22.4°N/120°E and it runs dry after ~3 days, and outside either bound the key is **missing
from the response entirely**, which `fetch_forecast()` would reject; `jma_seamless` is
identical to MSM where MSM reaches and falls back to GSM elsewhere, so the key always
exists. Suffixing only happens with two or
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

`google_new_url.html` is the browser port (see "Demo pages"): it fetches the search RSS feed
for a keyword, sorts items by `<pubDate>` newest-first, takes the first N (default 20), and
resolves each `<link>`. It is a third parallel implementation of the resolve logic — change
it and the `.py`/`.mjs` together — with two deliberate divergences, both forced by the
browser:

- **Batched RPC.** The scripts do one POST per link; the page collects all signatures first
  and sends them in one `batchexecute` POST (chunked at 20, `RPC_CHUNK`). Response rows come
  back **out of order**, tagged with the request id in `row[6]` — match on that id.
  Positional matching looks fine and silently pairs the wrong URL with the wrong row.
- **CORS proxy.** `news.google.com` sends no `Access-Control-Allow-Origin`, so *every*
  request (feed, article pages, RPC POST) is routed through a proxy chosen from a dropdown
  of public services, plus a custom-template field (`{url}` encoded, `{raw}` verbatim). This
  is the fragile part: free proxies return 5xx, rate-limit after a handful of calls, and
  some drop POST bodies (which passes step 1 and fails the whole resolve). Failures are
  surfaced per row rather than aborting the run. Do not "fix" a failing demo by rewriting
  the logic — check the proxy first.

Two details that are load-bearing: article URLs are requested with
`&hl=en-US&gl=US&ceid=US:en` appended, because the bare URL answers `302` to exactly that
URL and not every proxy follows redirects; and each article page is ~570 KB (the signature
is scraped from it), so the default 20 links move ~12 MB through the proxy — hence the
worker pool and the 中止 button. `data-n-a-ts` is page-render time, not per-article, but
`data-n-a-sg` is signed per article, so the per-article GET cannot be skipped.
