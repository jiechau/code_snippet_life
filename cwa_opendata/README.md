# cwa_opendata

Query Taiwan CWA (Central Weather Administration) Open Data for daily sun and moon
rise/set times, and print a one-line summary.

Data source: <https://opendata.cwa.gov.tw/>

| Script | Dataset | What it does |
| --- | --- | --- |
| `cwa_sunrise.py` | `A-B0062-001` | Sunrise / sun transit / sunset time and azimuth/altitude for a county on a date, plus daylight length. |
| `cwa_moonrise.py` | `A-B0063-001` | Moonrise / moon transit / moonset for a county on a date, plus time the moon is up. |

## How it works

Both scripts hit the CWA REST datastore endpoint
`https://opendata.cwa.gov.tw/api/v1/rest/datastore/<dataset-id>` with query
parameters `Authorization` (API key), `format=JSON`, `CountyName` (e.g. `臺北市`),
`timeFrom` / `timeTo` (a date window), and `sort=Date`, then read the daily records
from `records.locations.location[0].time`.

- **Sun** is simple: fetch a 1-day window and use that day's record directly.
- **Moon** needs care: the moon rises ~50 minutes later each day, so on any given
  date one of rise/transit/set may be missing (empty string in the API response) or
  belong to an adjacent calendar day. The script fetches a 3-day window
  (yesterday/today/tomorrow) and stitches together the full rise→transit→set cycle
  that starts on the target day, prefixing times taken from adjacent days with
  `昨` (yesterday) or `明` (tomorrow).

## Demo pages

Both scripts have a browser port, listed on [`index.html`](index.html):

| Page | Demo of |
| --- | --- |
| [`cwa_sunrise.html`](cwa_sunrise.html) | `cwa_sunrise.py` |
| [`cwa_moonrise.html`](cwa_moonrise.html) | `cwa_moonrise.py` |

Each fills in the request, prints the one-line summary its script prints, and
shows the request URL and the exact JSON that came back. They are **parallel
implementations** of the scripts — change the window or the formatting in one and
mirror it in the other. Verified against the Python across 7,518 comparisons
(7 counties × three 180-day windows, both datasets): every sunrise line, and every
moon branch pick and summary, identical. Each page is also run end to end against
a DOM stub and the live API — 54 assertions covering defaults, the county pills,
the key round-trip, both HTTP-200 emptinesses and a bad key.

Unlike every other demo in this repo these pages need a **credential**, and a
static page has no environment variable and no `config.yml` to read — so the key
is a **box on the form**. Two checkboxes sit beside it:

- **顯示金鑰 (show key)** — reveals it in the field *and* in the displayed URL.
  Both are hidden by default, because the key travels in the query string, which
  makes the request URL itself the credential; masked, the URL box is plain text
  rather than a link, since the string on screen is not one that would work.
- **記住金鑰 (remember)** — keeps it in this browser's `localStorage` so the next
  visit has it filled in already. **Opt-in and off by default**: unticked, nothing
  is written; unticking again deletes it at once. `localStorage` is per-origin, so
  both pages here share one entry while the published GitHub and GitLab copies
  remember separately, and nothing ever leaves the browser. Every access is
  wrapped in `try`/`catch` — Safari throws outright on `file://`, and a browser set
  to block site data throws on read as well as write — so the feature degrades to
  "the box starts empty" instead of taking the page down.

No cookie is set either way, and the key is never sent anywhere but
`opendata.cwa.gov.tw`.

## API quirks these pages have to handle

- **A wrong key looks like a network failure, not a 401.** CWA answers a bad key
  with `HTTP 401 Forbidden: Authorization key is not correct.`, and that response
  carries **no** `Access-Control-Allow-Origin` header — though a successful one
  does send `*`, which is the only reason a browser demo is possible at all. So
  the browser refuses to hand the 401 to the page and `fetch()` rejects before the
  status can be read. Both pages say so where a lesser message would blame the
  network.
- **`timeTo` is exclusive.** One day is `timeFrom=D`, `timeTo=D+1`; passing the
  same date twice returns nothing at all. A window is also capped at **180
  records** however wide it is asked for.
- **Coverage runs about 2025-01-01 to 2027-12-31.** Outside it the response is a
  perfectly ordinary `HTTP 200` with `success: "true"` and an empty `time` array.
- **An unmatched county is also HTTP 200**, with `locations.location` empty. The
  commonest cause is the wrong character: the API spells it **臺**北市, not 台北市,
  and does not know the abolished 臺北縣 — which is why the pages offer the 22
  county names as buttons rather than trusting anyone to type them.

## The `"00:00"` ordering bug, and CWA's blank records

`pick_moon_events()` used to fail on 27 of 3,738 target days (7 counties × three
180-day windows) — 26 raising `ValueError: invalid literal for int() with base 10:
''` out of `_moon_up()`, and one printing a mangled
`出:18:41/120,中:明/,沒:明05:21/241 (10:40)`. There were two causes, and only one
was a bug:

**A real bug, now fixed.** A transit or set stamped exactly `"00:00"` is the
rounding of 23:59:xx — the *end* of that date — but compared as a string it sorts
before every other `"HH:MM"`, which sent the branching off to borrow the event
from a neighbouring day that had none. `_order_key()` reads it as `"24:00"` for
the two order-sensitive comparisons, and those days now resolve into complete
cycles: 連江縣 2027-02-13 goes from a crash to
`出:10:07/69,中:17:00/84S,沒:00:00/294 (13:53)`, and 澎湖縣 2025-07-10 from
`中:明/` to `中:00:00/39S`. It is deliberately **not** applied to the rise — a rise
at `00:00` really is just after midnight (six of them in the same three years),
and normalising it would misorder the cycle the other way.

**Not a bug: CWA has no data.** It publishes an occasional **wholly blank record**
— all three times empty, the angles still filled in — about once a synodic month
at 澎湖縣 (12 in three years, each spoiling two target days, since the day before
one borrows its set), and very rarely two consecutive days with no rise (連江縣,
2026-07-09). Nothing in a three-day window can recover those. They now travel as
empty strings and print as `–`, via `_format_event()` and a `_moon_up()` that
returns `–` rather than raising. That is 25 of 3,738 days.

Verified: of the 3,738 windows, **3,711 are byte-identical to before**, 26 no
longer raise, and exactly one output changed — the mangled line, now correct.
`cwa_moonrise.html` mirrors all of it; its `incompleteCycle()` is display-only
now, naming the missing events in the note under the answer so a `–` reads as
CWA's gap rather than a fault here.

## Running

```bash
# defaults: 臺北市, today (Asia/Taipei)
uv run cwa_sunrise.py
uv run cwa_moonrise.py

# specific county / date
uv run cwa_sunrise.py 高雄市 2026-07-15
uv run cwa_moonrise.py 高雄市 2026-07-15
```

Example output:

```
臺北市 2026-07-15
出:05:14/64.66,中:11:58/84.51,沒:18:43/295.39 (13:29)
```

## API key

The scripts read the API key from (in order):

1. the `CWA_API_KEY` environment variable, or
2. `config.yml` at the repo root (gitignored) — copy `config_example.yml` to
   `config.yml` and fill in your key:

   ```yaml
   cwa_opendata:
     api_key: CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
   ```

The demo pages have neither route available to them, so they take the key from a
form field instead (see above).

Free registration at <https://opendata.cwa.gov.tw/>.
