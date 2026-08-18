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
  introduce cross-snippet imports or a shared root package. **There is exactly one
  sanctioned exception:** root `places.js`, the saved stargazing spots shared by all
  three demo pages (see below). Do not widen it — nothing else moves to the root.
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
`favicon.svg`, `places.js`, `robots.txt` and each demo folder into `public/`, while
`.github/workflows/deploy.yml` uploads the whole tree — both on push to `main`/`master`.
Navigation is two levels of list page: root `index.html` links to one
`<snippet>/index.html` per snippet folder, and that folder list links to one page per
demo, **named after the script it ports** (`open_meteo/open-meteo.html` ports
`open_meteo/open-meteo.py`); an alternate view of the same script adds a `_suffix`
(`open-meteo_readable.html`). Two pages have no script to be named after:
the two `astro_score/astro-score_*.html` pages are forks of
`open_meteo/open-meteo_readable.html` rather than ports of one script, so they take
their folder's name, and `bigdatacloud/reverse-geocode.html` is named after the
endpoint it calls because `bigdatacloud/` holds no script at all. List pages carry no logic — they are the same small card
markup, differing only in title and links.

**Adding a demo means: a `<snippet>/<script-name>.html` page, a link on that folder's
`index.html`, a row in the root `README.md` "Demo pages" table, and — if the snippet
folder is new to Pages — a link on the root `index.html` plus the folder added to the
`cp -r` line in `.gitlab-ci.yml`** (the GitHub workflow uploads the whole tree and needs
no change).

Pages hosting is static, so a demo page **cannot run the snippet's Python**. It is a
JavaScript re-implementation that calls the upstream API directly from the browser, which
makes it a parallel implementation under the rule above: change one, mirror the other.
This is effortless for keyless, CORS-enabled APIs (Open-Meteo, BigDataCloud's
`-client` endpoints). `cwa_opendata` needs an
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

Plain Open-Meteo API demo: `open-meteo.py` and its two browser ports,
`open-meteo.html` (raw JSON, listed as **open-meteo API**) and
`open-meteo_readable.html` (hour-by-hour grid). The stargazing scorer that used to
live here is now `astro_score/` — see below; the two folders are deliberately
independent copies, not a shared library, per the one-folder-per-snippet rule.

**`open-meteo.html` shows the API response and nothing else.** It has no
`reverseGeocode()` / `appendPlaceName()` — that was deliberately stripped so the
page reflects only what Open-Meteo returned.

**Neither `open_meteo/` page shows anything Open-Meteo did not return.** The same
rule was then applied to `open-meteo_readable.html`: its place name and its
`太陽`/`月亮`/`月相` rows are gone too, and the Meeus astronomy went with them. What
the grid draws is API series and nothing else. Do not reintroduce a second service
or a locally computed row here — `astro_score/astro-score_readable.html` is where
both belong, and it still has them.

That is why `is_day` is in `HOURLY_VARS`: the 天氣 glyphs need day from night, and
with no local solar altitude left, the API's own series is the only source. It is
the eleventh variable, one more than `open-meteo.py` asks for. If `is_day` is
dropped from the hourly box the glyphs fall back to the daytime set rather than
guessing from the hour.

`open-meteo.py` is the bare API demo: it builds the request URL itself with
`urlencode(params, safe=",")` and requests that exact string, so the `get_para` key it
adds to the response is the real URL rather than a reconstruction (`requests` would
percent-encode the commas in the `hourly`/`models` lists). It returns API errors instead
of raising, prints request metadata to stderr so stdout stays pipeable JSON, and exits 1
on a non-2xx. Note the filename is hyphenated, so it is a script only — not importable.

`open-meteo.html` reproduces the script's URL construction exactly —
`encodeURIComponent` with `%2C` mapped back to a literal comma and `%20` to `+`, matching
`urlencode(params, safe=",")` byte for byte — so `get_para` stays the real request URL.
Like the script, it displays an API error body instead of throwing.

`open-meteo_readable.html` issues the same request and renders the response as an
hour-by-hour grid: a tab per model, a row per `hourly` variable, colour-graded cells, a
sticky label column and horizontal scroll. It is the page that has to cope with the
suffixing rule at runtime, so `seriesKey()` accepts both `<var>_<model>` and bare `<var>`.
Two API quirks it handles and that any similar page will hit: a model that does not
publish a variable still returns a key — nulls all the way down, with the unit reported as
the **literal string `"undefined"`** (so with the default four models, three of the
`visibility` tabs are a row of dashes) — and `forecast_days` starts the series at 00:00
local, so past hours are trimmed using `utc_offset_seconds` (the 從現在開始 checkbox).

Row labels are deliberately terse (`LABELS`, `API_SHORT`, `UNIT_SHORT`): the label column
is `position: sticky`, so its width is subtracted from every scroll position — abbreviating
took it from 184px to 103px and bought two more hours on screen, which matters most on a
phone. The full API name lives on the `title` attribute, and an unlisted variable falls
back to its own (long, but never wrong) name. Keep new labels to two or three CJK
characters.

`DEFAULT_EXTRA` prefills two lines into the extra-params box — kept there, not in
`defaultParams()`, so the request core stays identical to the script:

- `daily=sunrise,sunset,moon_phase`. **Model suffixing applies to `daily` as well as
  `hourly`**, so four models return twelve daily series; they are pure astronomy, so every
  model's `moon_phase` is byte-identical and sunrise/sunset differ only by grid-point
  rounding. The readable grid renders `hourly` only, so this surfaces in the raw JSON panel
  alone — no `open_meteo/` page reads it, so clearing the line changes nothing on screen.
  It is pure cross-check material now that the grid has no sun/moon rows of its own; the
  extra-params hint on both pages says so.
- `past_days=7`, which takes the response from ~33 KB / 168 hours to ~64 KB / 336 hours
  (billing counts time range, not just variables). The API accepts `past_days` up to **93**,
  but the models keep only a rolling ~2-month archive (the JMA models shortest,
  `ecmwf_ifs025` longest), so **~61 is the practical maximum** — beyond it the extra hours are nulls. At 61
  the response is ~300 KB / 1632 hours and the 從現在開始 trim is what keeps the grid usable:
  unticked that is 68 day groups, ~24,500 cells. Anything iterating the whole series should
  assume that scale is reachable from the form.

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

`PLACES` drives both the default location and the buttons beside the location box, and it
lives in **root `places.js`**, not in the pages — each page loads it with
`<script src="../places.js"></script>` immediately before its own inline script, and
`DEFAULT_LAT`/`DEFAULT_LON` are destructured from `PLACES[0]` in that same file. Adding,
removing or reordering a spot is a one-line change there and nowhere else, and reordering
changes what every page opens on. It is a **classic script on purpose** — `type="module"`
would be fetched under CORS rules and break `file://`, which the READMEs offer as a way to
run the pages with no server; a top-level `const` in a classic script is visible to the
inline script that follows it. Because it sits outside the demo folders, `.gitlab-ci.yml`
needs its own `cp places.js public/` line (the GitHub workflow uploads the whole tree).
Clicking a button fills the box **and refetches** — leaving a stale result under a new
location would misrepresent it. The buttons only reflect the box, so a hand-typed
coordinate leaves all of them unpressed. Note a click while a fetch is in flight is a
silent no-op: `requestSubmit()` does nothing while the submit button is disabled.

## What is duplicated across the demo pages

There are **five demo pages** (ignoring `google_news_url`, which shares nothing),
four of them built on one Open-Meteo request core, and no shared file except
`places.js` — by the one-folder-per-snippet rule, keeping them in step is a manual
discipline. They are `open_meteo/open-meteo.html`,
`open_meteo/open-meteo_readable.html`, `astro_score/astro-score_readable.html`,
`astro_score/astro-score_daily.html` and `bigdatacloud/reverse-geocode.html`. Know
which blocks are copies before editing any of them:

| Block | Copies |
| --- | --- |
| Request core (`buildUrl`, `fetchForecast`, `FORECAST_URL`) | the 4 Open-Meteo pages + `open_meteo/open-meteo.py`; `bigdatacloud/` has the same `buildUrl` shape against its own endpoint |
| `paramsFromForm()` | the 3 pages with a location box; `astro-score_daily.html` has `paramsFor(lat, lon)` instead — its rows *are* the places, so there is no location to parse |
| Page chrome (whole `<style>` block, `show()`, submit handler) | `open_meteo/open-meteo.html` + `bigdatacloud/reverse-geocode.html` — the latter is that page with the form cut to one field |
| `.locrow`/`.place` CSS, `buildPlaces()` / `markActivePlace()` | 4 pages — **not** `astro-score_daily.html`, which has no location box to put buttons beside |
| `PLACES` | **not duplicated** — root `places.js`, loaded by all 5 pages. `DEFAULT_LAT`/`DEFAULT_LON` from that file are unused by `astro-score_daily.html` |
| The `countryName/principalSubdivision/city/locality` join | `astro_score/astro-score_readable.html` (`reverseGeocode()`) + `bigdatacloud/reverse-geocode.html` (`placeName()`) |
| `reverseGeocode()` / `appendPlaceName()` (the *deferred, never-awaited* lookup) | `astro_score/astro-score_readable.html` only; **never** either `open_meteo/` page |
| Meeus solar/lunar series | both `astro_score/astro-score_*.html` pages + `astro_score/milkyway.py` — all in `astro_score/`, none in `open_meteo/`. `astro-score_daily.html` carries only what it draws: no `GC_RA`/`GC_DEC` and no `moonIllumination()` |
| `DARK_SUN_ALT`, `MOON_KILL_ALT`, `moonPenalty()`, `astroScore()` | both `astro_score/astro-score_*.html` pages, verbatim |
| `LABELS`, `API_SHORT`, `UNIT_SHORT`, `tint()`, `SCALES`, hour-grid rendering | the 2 hour-by-hour grid pages only — `astro-score_daily.html` draws days as bars, not variables as tinted cells, and has none of them; `open-meteo.html`/`reverse-geocode.html` draw no grid at all |
| `HOURLY_VARS`, `MODELS`, `DEFAULT_LAT`/`DEFAULT_LON` | `open-meteo*.html` only — both `astro-score_*.html` pages deliberately override these |
| The extra-params box + its `key=value` parse loop | all 4 Open-Meteo pages, the loop verbatim. `DEFAULT_EXTRA` is **not** shared: `open-meteo*.html` prefill `daily=...` **and** `past_days=7`, both `astro-score_*.html` prefill `past_days=7` alone (nothing there reads `daily=`) |

**Edit one and you must edit the others in its row.**

The Meeus row is the strictest: the JavaScript is **verified to agree with `milkyway.py`
to four decimal places**, so changing the astronomy in either means re-checking both. `julianDay()` uses the Unix epoch (JD 2440587.5) instead of the Python's
Gregorian calendar arithmetic; the two are exactly equivalent.

`reverseGeocode()` puts `countryName/principalSubdivision/city/locality` (e.g.
中華民國/宜蘭縣/南澳鄉/蘇澳鎮) on a **second meta line** from BigDataCloud's keyless,
CORS-enabled `reverse-geocode-client`. The break is a `<br>` node appended to the
element, not a `\n` in the text — `.meta` wraps normally, so a newline would render
as a space. It is sent the **requested** lat/lon, not the response's grid point — the two
can name different townships. The lookup is fired after the result renders and never
awaited, so it re-checks the meta text before appending and skips it if a newer fetch has
replaced the line; any failure resolves to an empty string and leaves the line alone. It
is a label, never data: nothing on screen depends on it. Only
`astro_score/astro-score_readable.html` has it; both `open_meteo/` pages deliberately do
not, so their meta line says exactly what `open-meteo.py` prints to stderr and no more.
`bigdatacloud/reverse-geocode.html` demos the same endpoint head-on, and its copy of the
four-field join is the one thing the two pages share.

## astro_score specifics

Stargazing and Milky Way scoring: `milkyway.py` and two demo pages,
`astro-score_readable.html` (listed as **AstroScore readable**) and
`astro-score_daily.html` (**AstroScore daily**). The first was `milkyway_readable.html`
until the folder was renamed; two carried-over forks of the `open_meteo/` pages were
deleted at the same time. Both are named after the folder rather than a script because
they are forks of `open_meteo/open-meteo_readable.html`, not ports of one script. See the
duplication table above before editing either.

The two answer different questions and that is the whole reason both exist:
`astro-score_readable.html` is **which hour tonight, at one place**;
`astro-score_daily.html` is **which place, which night**. Don't merge them, and don't
add hour detail to the daily page — the readable page is one click away and is where
hour detail belongs.

**Its user-facing vocabulary is 觀星 / AstroScore, not 銀河 / milky way** — the score row
is `觀星 (%)` with the API sub-label `AstroScore`, and the scoring function is
`astroScore()`. Only comments that point at the Python file still say `milkyway.py`, which
is correct: that file kept its name.

`astro-score_readable.html` is the `*_readable` grid stripped to what stargazing needs. It
fixes `hourly` (the four cloud decks, plus `precipitation_probability` and
`temperature_2m` — 降雨 and 氣溫, which `astroScore()` does not read but a human picking a
night does) and `models` (`icon_global` alone), removing those two textareas from the
form; `forecast_days`, `timezone`, **extra params** and the location remain. One model
means no tabs and **bare series keys**, which `seriesKey()` already resolves, and the
response drops to ~7.0 KB / 168 hours from ~64 KB / 336.

Its `DEFAULT_EXTRA` is **one line, `past_days=7`** — not the `open_meteo/` pair, since no
page here reads `daily=`. It is deliberately invisible in the default view: the 從現在開始
trim hides every past hour, so the grid looks the same until the box is unticked, and then
it shows the week just gone — a forecast next to what the sky actually did. It costs the
response ~7.0 KB / 168 hours → ~13 KB / 336. Since `hourly`/`models` are fixed here, this
is the only free-form parameter box on the form, which is why it survived the strip. The 觀星 row goes between 時間 and 天氣, green
label, tinted `[0, 100, false]` so 100 is green, and the `銀心` row sits between the
two — galactic core altitude from the same `GC_RA`/`GC_DEC` as `milkyway.py`, tinted
`[0, 25, false]` after that file's `core_up` ramp. It is drawn by `drawAstroRow()`,
the same routine the `ASTRO_ROWS` below 天氣 use, and is **display only**:
`astroScore()` does not read it, so a core below the horizon does not lower the score. Its score is
`(100 − 雲量) × (100 − moonPenalty) / 100`, zeroed outright when the sun is above −10°,
where `moonPenalty` ramps 0→100 as moon altitude goes 0°→10° (`MOON_KILL_ALT`) and is 0
below the horizon — altitude only, so 月相 is left on screen to judge illumination by eye.
The moon used to be a hard `> 0° → 0` cutoff; the ramp exists because that threw away the
best hour of nights when a low moon was setting, so **don't "simplify" it back**. The score
is **deliberately not** a port of `sky_quality()` — a rule of thumb the user is still
revising, so the two are free to disagree. The astronomy underneath it is the shared part,
and is not.

### astro-score_daily.html

A week for every saved spot at once: **a row per `PLACES` entry, a column per day**, and
each cell **two** block glyphs — `▂ ▄ ▆ █` or blank — one per half-day (00–11 / 12–23,
left to right, local time). A block's value is the **maximum** 觀星 in it, i.e. its best
single hour on the plain 0–100 scale, and that peak picks a height: `>90` `█`, `>70` `▆`,
`>50` `▄`, `>30` `▂`, at or below 30 blank. Thresholds are **strictly greater** — a peak
of exactly 90 draws `▆`.

Max rather than sum or average is the point: the grid answers "is there an hour worth
going out for", and one excellent hour justifies the drive even when the rest of the night
clouds over. The cost is that a bar says nothing about how *long* the window lasts —
that is what the readable page is for, and the daily page should not grow a second
encoding to say it.

Half-days rather than quarter-days because each then holds exactly one dark stretch (the
daylight half scores 0 and cannot touch a maximum), which is also why the split is at noon
and not midnight. **A night therefore straddles two cells**: the right glyph of one day is
that evening, the left glyph of the next is its small hours. One clear night reads `…█|█…`
across a column rule, *not* as `██` inside a single cell — a cell showing `██` is the tail
of one night beside the head of the next. Any prose added here must keep that straight; it
is the one thing about this grid a reader gets wrong.

Its form is `forecast_days`, `timezone` and an **extra params** box prefilled
`past_days=7`, applied to every request alike — so a typo there costs one call per saved
place,
and `paramsFor()` is therefore called for every place *before* the button is disabled, so
a malformed line reports itself with nothing sent. `past_days` on a day grid means extra
columns to the **left** of today, hidden until 從今天開始 is unticked. Each past day is
~540 bytes per place, taking a nine-place round from ~36 KB to ~69 KB.

It issues **one request per spot** (`Promise.allSettled`, so one failure costs one row,
which then shows the API's own reason in place of its glyphs) and asks for `cloud_cover`
alone — `astroScore()` reads nothing else and the page displays no number a human reads
directly, so the 降雨/氣溫 that `astro-score_readable.html` carries for exactly that
reason would be one response of undrawn data per place. Each response is ~4.0 KB / 168
hours (mostly the timestamps), so at the nine spots `places.js` currently holds that is
~36 KB the round. **The count follows `places.js`** — it was seven when this page was
written, so treat any figure here as "per place × however many spots are saved".

Consequences of having no location box: no `paramsFromForm()` (it has `paramsFor(lat,
lon)`), no `buildPlaces()`/`markActivePlace()`, no `.locrow`/`.place` CSS, and
`DEFAULT_LAT`/`DEFAULT_LON` go unused. It also has no `GC_RA`/`GC_DEC` and no
`moonIllumination()`: the astronomy it copies is only what the score needs. The block
glyphs are **fixed-width `<span class="bar">` elements, not a monospace string** — a blank
block is an empty span, and an empty character in a proportional run would collapse and
shift the rest of the cell. They sit on the baseline so the four grow out of a common
floor and read as a bar chart. They are packed **tight**: `.bar` is `width: 1ch`, which in a
monospace face is exactly one character advance, so the block glyphs tile with no seam
(the earlier `0.62em` was a guess and left a hairline gap). `td.blocks` has **zero
horizontal padding**, and `th, td` carries **no `min-width`** — a floor wider than the
content would reintroduce as dead space exactly the gap the tight packing removes.

The column header is the other half of that: the date is **stacked, `08` over `18`, not
`08/18`** (`dateLines()`, two `display: block` spans, monospace), so it is two characters
wide like the two glyphs beneath it and every column in the grid is a 2-character column.
Flat `MM/DD` was the widest thing in the column and it, not the bars, set the width. At
`0.8rem` the header now sits centred *inside* the ~29px the bars occupy; raising it to
`1.5rem` would make the digits span the bars exactly, at the cost of a heavy header row.
`formatDate()` still returns flat `08/18` — the cell tooltip has room for a slash. Across a row the only thing between one day's
bars and the next day's is the 1px column rule. **Every bar is one green** (`var(--ok)`, the 觀星 green) at
every height, and this page has **no `tint()`** — that lives in the two hour-grid pages,
which draw tinted number cells; here a bar's height is already its value. Grading the colour by the same number stated it twice and stated it
worse: the green-to-red sweep turned a short bar brown, which read as a different *kind* of
thing rather than as less of the same one. Don't reintroduce a per-cell colour scale here.

Its checkbox is **從今天開始 (hide past days)**, and it is the sibling page's 從現在開始
moved up from hours to days, because a column here is a day. It **drops whole past
columns**; it never shortens a column it shows, so today is always a full 24 hours and a
block does not shrink as the afternoon wears on. Hiding rather than zeroing is the point:
zeroed past days drew as blank glyphs and pushed today off the right of a phone screen.
`blocksByDate()` therefore takes no "now" argument at all — it scores every hour it is
given, and `visibleDates()` alone decides what is drawn. Each cell's `title` reports every
block's sum and, when fewer than six hours were scored (a null cloud figure, a short
response), how many were counted.

"Today" comes from the response's `utc_offset_seconds` (`localToday()`), **not** the
browser clock, so a hand-typed `timezone=` in the extra params moves the today column with
it. Column headers carry no weekday — just the stacked date (see the packing note above).

Grid lines are two weights, and the distinction is deliberate. Every column gets a hairline
`--grid` (`#eef1f4`, lighter than `--line`) so four glyphs in open space do not bleed into
the next day; **today** gets a 2px rule down the full height — the same `.daybreak` idiom
`astro-score_readable.html` uses at date boundaries — dividing what happened from what is
forecast. That heavier rule is only applied when a past column actually precedes today,
i.e. when 從今天開始 is unticked; as the first column it would just double the label
column's own border.

`milkyway.py` scores each upcoming hour for Milky Way astrophotography at a `lat,lon`.
No API key — Open-Meteo's free tier is keyless (10,000 calls/day), so there is nothing to
read from `config.yml`. It queries `hourly=` cloud/moisture variables with
`&models=icon_global,jma_seamless,gfs_global,ecmwf_ifs025`, which suffixes every series with
its model name (`cloud_cover_gfs_global`) — and not every model publishes every variable
(of the four, **only gfs returns `visibility`**; `precipitation_probability` is null for
jma), so `_hour_vars()` fills gaps from the ensemble mean, which for `visibility` means
gfs on its own. The model list is shared with `open_meteo/open-meteo.py` and both
`open_meteo/open-meteo*.html` pages (**not** `astro-score_readable.html`, which fixes
`icon_global` alone), and its order is the order rows/tabs appear in, so keep the four in
step across both folders. `jma_seamless` rather
than `jma_msm` is deliberate: MSM is 0.05° ≈ 5 km over Taiwan but its domain stops near
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

## bigdatacloud specifics

Reverse geocoding with BigDataCloud, and the only snippet folder with **no script** —
just `reverse-geocode.html` (listed as **reverse-geocode API**) and the folder
`index.html`. The call is one keyless `GET` to
`https://api.bigdatacloud.net/data/reverse-geocode-client` with
`latitude`/`longitude`/`localityLanguage`, so a Python version would demonstrate
nothing the page does not; the page is named after the endpoint rather than a script.

The page is `open_meteo/open-meteo.html` with the form cut to its single input — same
`<style>` block, same `buildUrl`/`show()`/submit-handler shape, same policy of
*displaying* an API error body rather than throwing. `localityLanguage` is a **constant
in the page, not a field**: the user asked for location as the only input, so changing
the language means editing `LOCALITY_LANGUAGE`. Unlike `open-meteo.html` there is **no
`get_para`** added to the body — that key exists because `open-meteo.py` adds it, and
there is no script here — so the JSON pane is byte-for-byte the response and the URL
lives only in its own box.

The one derived thing on screen is the second meta line,
`countryName/principalSubdivision/city/locality` joined with blanks and duplicates
dropped: a copy of `reverseGeocode()` in `astro_score/astro-score_readable.html`, kept
because it is the payoff of the call (four fields out of a ~2.8 KB response, shown
beside the response). It runs inline in `show()` rather than as the deferred,
never-awaited lookup `astro_score` needs — there the forecast is already on screen and
the name must not block it; here the name *is* the result. Change the join in either
page and change the other.

Response quirks the page and README both note: `postcode` is empty for Taiwan; `city`
repeats `principalSubdivision` in directly administered municipalities (臺北市/臺北市,
which is why the join dedupes); `localityInfo.administrative` is most of the bytes and
carries the PRC's naming for Taiwan (`中国台湾`, `CN-TW`) alongside
`countryName: 中華民國`; and a bad coordinate answers **HTTP 400** with a body whose own
`"status"` says **401**, so the meta line reports `resp.status` and not the body's.

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
