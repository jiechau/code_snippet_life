# open_meteo

Snippets built on the [Open-Meteo](https://open-meteo.com/) weather API.
**No API key required** — the free tier allows 10,000 calls/day, 5,000/hour and
600/minute for non-commercial use. Requests are billed fractionally: more than 10
weather variables counts as more than one call, so one `open-meteo.py` run (10
variables × 4 models) bills as a few calls.

**API reference: <https://open-meteo.com/en/docs>** — every variable name used in
`hourly=` / `daily=`, the model ids for `models=`, the units each field comes back
in, and the interactive URL builder. Worth opening alongside the demo pages: it is
the list to pick from when editing their `hourly` or `extra params` boxes.

**Live demo:** https://jiechau.github.io/code_snippet_life/open_meteo/

- [open-meteo API](https://jiechau.github.io/code_snippet_life/open_meteo/open-meteo.html)
  — one call, raw JSON plus the request URL.
- [open-meteo readable](https://jiechau.github.io/code_snippet_life/open_meteo/open-meteo_readable.html)
  — the same call as an hour-by-hour grid.

The stargazing scorer that used to live here — `milkyway.py` and its grid — moved
to [`astro_score/`](../astro_score/README.md); this folder is now the plain API
demo and nothing else.

## The four models

Everything in this folder sends the same `&models=` list, as does
`astro_score/milkyway.py`. These are four
completely separate forecasting systems, each run by
a different national or intergovernmental weather agency, not four views of one
dataset:

| id | Agency | Country | Resolution over Taiwan | New run |
| --- | --- | --- | --- | --- |
| `icon_global` | DWD (Deutscher Wetterdienst) | Germany | ~11 km | every 3 h |
| `jma_seamless` | JMA — MSM where it reaches, GSM beyond | Japan | 0.05° ≈ **5 km** | every 3 h |
| `gfs_global` | NOAA / NCEP — Global Forecast System | USA | 0.25° ≈ 25 km | every 1 h |
| `ecmwf_ifs025` | ECMWF (European Centre for Medium-Range Weather Forecasts) | EU / intergovernmental | 0.25° ≈ 25 km | every 6 h |

Open-Meteo's docs list each model *family*, so its quoted resolution ranges fold
in high-resolution regional nests (HRRR for GFS, ICON-D2 for ICON) that only
cover the US and Europe. The `_global` variants are used here precisely because
those regional nests do not cover Taiwan.

**`jma_seamless` is the exception, and the reason it is in the list.** JMA's
regional nest — MSM, 0.05° ≈ 5 km, hourly native fields — *does* reach Taiwan,
and at 11× the grid resolution of the global models it is the only member that
can resolve the Central Range at all. Its domain stops around 22.4°N / 120°E,
though: ask for `jma_msm` at 墾丁 (21.95, 120.80) and the series is **absent from
the response entirely** — not null — which would trip `fetch_forecast()`'s shape
check. MSM also runs dry after ~3 days. `jma_seamless` is the safe way to get it:
it is byte-identical to `jma_msm` inside the domain and falls back to GSM
(0.5° ≈ 55 km, 6-hourly) outside it and beyond day 3, so the key always exists
and `forecast_days=7` comes back complete. It replaced a bare `jma_gsm`, whose
55 km cells spanned the whole Central Range.

**How independent are they?** Partially. They all assimilate largely the same
raw observations — satellite radiances, radiosondes, aircraft reports, buoys —
shared internationally over the WMO Global Telecommunication System. Where they
genuinely diverge is data assimilation and **physics parameterization**. That
second one is what matters here: clouds are mostly smaller than a grid cell, so
no global model resolves them; each estimates cloud fraction from humidity,
stability and convection with its own empirical scheme, and those schemes
disagree a lot. Cloud cover is among the least skillful fields in numerical
weather prediction, which is the whole reason for querying four models.

Rough reputations:

- **ECMWF** consistently verifies best in global headline scores — the model
  meteorologists reach for first.
- **ICON** has a good name specifically for cloud and boundary-layer detail.
- **JMA** has home-field advantage for East Asia and typhoons, and via
  `jma_seamless` the finest grid of the four over Taiwan.
- **GFS** is the freshest, updating hourly, and the most permissively open.

Note this is a **multi-model** ensemble — four models, one run each — not a
single-model ensemble, where one model runs 30–50 times with perturbed initial
conditions. Open-Meteo exposes those separately via its Ensemble API
(`ensemble-api.open-meteo.com`). Nothing in this folder combines the four into a
single number; `astro_score/milkyway.py` does, and
[explains how](../astro_score/README.md#weighting-milkywaypy).

## `open-meteo.py`

A minimal demonstration of one API call. Prints the **exact JSON Open-Meteo
returned**, with a single key added — `get_para`, the full request URL.

```bash
uv run open-meteo.py                                   # defaults (Taipei, 7 days)
uv run open-meteo.py 24.1375,121.2745                  # set the location
uv run open-meteo.py 24.1375,121.2745 forecast_hours=24 # override any query param
uv run open-meteo.py models= hourly=cloud_cover        # empty value drops a param
```

With no arguments it submits the same request `astro_score/milkyway.py` makes. A bare
`lat,lon` argument sets the location; any `key=value` argument overrides or adds
a query parameter, and an empty value (`models=`) drops one entirely — useful
for watching the response shape change when the model list goes away.

```json
{
  "latitude": 25.0,
  "longitude": 121.5,
  "timezone": "Asia/Taipei",
  "hourly_units": { ... },
  "hourly": { ... },
  "get_para": "https://api.open-meteo.com/v1/forecast?latitude=25.033&longitude=121.565&hourly=cloud_cover,cloud_cover_low,...&models=icon_global,jma_seamless,gfs_global,ecmwf_ifs025&timezone=auto&forecast_days=7"
}
```

Request metadata goes to **stderr**, leaving stdout as clean JSON:

```
HTTP 200  application/json; charset=utf-8  31544 bytes  0.77s
```

```bash
uv run open-meteo.py > forecast.json
uv run open-meteo.py | jq '.hourly | keys'
```

Notes:

- `get_para` is the URL that was **actually requested**, not a reconstruction —
  the script builds the URL string first and sends that. Commas are left
  literal via `urlencode(params, safe=",")`; `requests` would otherwise encode
  them to `%2C`, which works but is unreadable. Paste `get_para` into curl or a
  browser and you get a byte-identical response back (modulo
  `generationtime_ms`).
- API errors are printed, not raised. Open-Meteo answers a bad request with
  HTTP 400 and a JSON body such as
  `{"error": true, "reason": "Latitude must be in range of -90 to 90°..."}`,
  which is more useful than a stack trace. `get_para` is added to the error body
  too, so you can see exactly what was sent. Exit status is 1.
- If both `forecast_days` and `forecast_hours` are present, **`forecast_hours`
  wins** — the API does not complain.

## `open-meteo.html`

Listed as **open-meteo API** on the folder's index page. A browser port of
`open-meteo.py` (see the root [`README.md`](../README.md#demo-pages)): submitting
fetches and re-renders the result below, showing the same one-line request summary
the script prints to stderr, the request URL as a clickable link, and the
pretty-printed JSON. **Nothing else** — see
[Nothing but the API](#nothing-but-the-api), which applies to both pages here.

The form is the same one `open-meteo_readable.html` uses — both pages open on the
identical request, so you can switch between raw JSON and the grid without
retyping anything:

- **forecast_days** and **timezone** share the first line.
- **hourly** and **models** — comma-separated; blank drops the parameter, which
  for `models` means bare series keys instead of model-suffixed ones.
- **extra params** — one `key=value` per line; an empty value drops a parameter.
  Prefilled with two:
  - `daily=sunrise,sunset,moon_phase` — the API's own sun/moon figures, and the
    only place they are used: they are echoed in the JSON as a cross-check, while
    the `太陽`/`月亮`/`月相` rows of `open-meteo_readable.html` are computed from
    the location by the page's own astronomy (the Meeus series ported from
    `astro_score/milkyway.py`), never read from the response. Clear the line and the grid is
    unchanged.
  - `past_days=7` — extends the series backwards a week, so a forecast can be read
    against what actually happened. It is not free: the response goes from
    ~33 KB / 168 hours to ~64 KB / 336 hours, and Open-Meteo bills by time range
    as well as variable count. Drop the line to go back to forecast-only.
    The parameter is accepted from 0 to 93, but **about 61 is the practical
    maximum**: the models keep a rolling archive of roughly two months
    (the JMA models the shortest, `ecmwf_ifs025` the longest), so days beyond that
    return nulls rather than data — at 61 the response is ~300 KB / 1632 hours,
    which is a lot of grid for hours you may not get.
- **location** — deliberately **last, immediately above Fetch**, because it is the
  only field normally touched: everything above it is left at its default, so the
  one control in constant use sits where the hand already is. A `lat,lon` box,
  narrow because that is all it ever holds, with **📍 使用目前位置** beside it and
  the saved spots wrapped onto a line of their own: 輸入, 瑞光路, 大武崙砲台, 內洞停車場, 烏石港, 東澳, 石梯坪, 加路蘭,
  龍磐公園, 合歡山, 柚子湖.
  Clicking one fills the coordinates and refetches; the pressed button shows which
  spot is displayed, and a hand-typed coordinate presses none. They come from the
  `PLACES` array in [`../places.js`](../places.js), shared by every demo page in the
  repo, whose first entry is also the default location — so adding, removing or
  reordering a spot is a one-line change **in that one file**, and it changes what
  all three pages open on.
- **使用目前位置 (use current position)** — the device's own GPS into the box, and
  into 輸入, `PLACES[0]`, the one entry that is not a saved spot; then it refetches
  like any spot click. Geolocation is a secure-context API, so it works on the
  published `https://` page and on `localhost` but not on `file://`, and a refusal
  (no permission, no fix, timed out) is printed beside the button rather than
  thrown. Nothing is stored: a reload, or Reset defaults, puts 輸入 back to the
  coordinate `places.js` was written with.

Four defaults deliberately differ from `open-meteo.py`: the location (三總 rather
than Taipei), the cloud decks listed high → low, the `daily=` line, and the extra
`is_day` variable — an eleventh alongside the script's ten, which
`open-meteo_readable.html` needs to tell day from night for its 天氣 glyphs and
which is kept here too so both pages still open on the identical request. The
request *machinery* is still a byte-for-byte port.

### Nothing but the API

Neither page here shows anything Open-Meteo did not return. There is no reverse
geocoding of the coordinates into a place name and no locally computed sun/moon
row: what is on screen is the response, and the meta line says exactly what
`open-meteo.py` prints to stderr. Both of those features exist — they are on
[`astro_score/astro-score_readable.html`](../astro_score/README.md), which is the
page that wants them. Keeping them out of this folder is the point of the split,
so please do not add a second service's data back in here.

The one consequence worth knowing: with no solar altitude computed in the page,
the 天氣 glyphs get day-vs-night from the API's own `is_day` series instead, which
is why `is_day` is in the default `hourly` list. Drop it from the box and the
glyphs fall back to the daytime set rather than guessing from the hour.

`index.html` is just the list page for this folder — one link per demo, reached
from the root hub. Each demo page is named after the script it ports, so a new
demo means a new `<script-name>.html` plus a row on `index.html`.

Open it locally with any static server (`python3 -m http.server`, then
<http://localhost:8000/open_meteo/>) or just open the file directly — it has no
build step and no dependencies.

## `open-meteo_readable.html`

The **same request** as `open-meteo.html`, using the identical form (saved spots
included — described under that page above), but the response is drawn as an
hour-by-hour forecast grid instead of raw JSON. The raw JSON and the request URL
are still there, in a collapsed `raw JSON & request URL` panel at the bottom. The
meta line above the grid adds the response's timezone, coordinates and elevation
to the request summary. That is the whole meta line — see
[Nothing but the API](#nothing-but-the-api).

What differs is everything below the form:

- **One tab per model.** The tabs come from the `models` field, and switching
  re-reads that model's series. This is where the suffixing rule shows: with two
  or more models the keys are `cloud_cover_gfs_global`, with one (or with
  `models` blank) they are bare `cloud_cover`. Both shapes render identically.
- **A row per `hourly` variable**, in the order requested, labelled in Chinese
  with the unit, and an abbreviated API name underneath (`precip` for
  `precipitation_probability`). The label column is frozen while the hours
  scroll, so its width costs a column of forecast at every scroll position —
  short names take it from 184px to 103px, worth two extra hours on screen. The
  unabbreviated name is on the cell's `title`, and an unrecognised variable
  falls back to its full API name, so adding one to the `hourly` box still
  works. Because
  row order follows request order, the default lists the cloud decks
  高雲 → 中雲 → 低雲 (top of the atmosphere downwards); `open-meteo.py` lists them
  low → high. Reorder the `hourly` box to reorder the grid.
- **A 天氣 glyph row** above the variables, from `cloud_cover` for the sky and the
  API's `is_day` for day vs night, so the icons switch to a moon after sunset. Both
  come out of the response; nothing on this grid is computed from the location.
  There are no `太陽`/`月亮`/`月相` rows — Open-Meteo has no hourly sun or moon
  altitude, only sunrise/sunset and a daily `moon_phase`, so those rows live on
  [`astro_score/astro-score_readable.html`](../astro_score/README.md) where they
  are computed from the Meeus series instead.
- **Colour is per variable**, green (good) to red (bad) on a per-variable range;
  a variable with no defined range is left uncoloured rather than tinted on a
  wrong scale.
- **Values a model does not publish show as `-`.** Only `gfs_global` returns
  `visibility` — the other three default models give a row of dashes — and
  `precipitation_probability` is null for `jma_seamless`. A model that does not
  publish a variable also reports the literal string `"undefined"` as its unit,
  which the page suppresses.
- **能見度 is ground-level viewing distance in metres**, derived by Open-Meteo
  from low cloud, humidity and aerosols rather than measured. It saturates at
  24140 m (15 miles, the unit gfs reports it in), so the row is mostly flat and
  dips when moisture builds. It says nothing about upper-air transparency: a
  night can read 24140 and still be overcast at 8 km, which is what the 雲量
  rows are for.
- **The prefilled `daily=sunrise,sunset,moon_phase`** is the only sun/moon data
  Open-Meteo has, kept next to the page's own calculations as a cross-check —
  the grid never reads it, so clearing the line changes nothing on screen.
  Its keys take the **same model suffixing as hourly ones**, so the four default
  models return twelve series — and since this is pure astronomy, every model
  returns the identical `moon_phase` with sunrise/sunset within a minute. The grid
  renders `hourly` alone, so this shows up in the raw JSON panel only.
- **從現在開始** drops the already-past hours — `forecast_days` starts the series
  at 00:00 local, the same trim `score_hours()` does in `astro_score/milkyway.py`. Local "now"
  comes from `utc_offset_seconds`. With the default `past_days=7` it hides the 168
  past hours, leaving ~150 of ~336; raise `past_days` to its practical maximum of
  61 and unticking shows all 1632, which is 68 day groups and around 24,500 cells —
  the browser copes, but it is a lot of grid to scroll.

It talks to Open-Meteo **straight from the browser**; Pages is static hosting and
cannot run the Python. That works only because Open-Meteo needs no API key (a key
would be visible in page source) and serves `access-control-allow-origin: *`.

Being a parallel implementation, it mirrors the script's behaviour: the same
defaults, the same literal-comma URL construction (`encodeURIComponent` with
`%2C` restored, matching `urlencode(params, safe=",")` byte for byte), the same
added `get_para` key, and the same policy of *displaying* an API error body
rather than throwing. Change one and mirror it in the other.
