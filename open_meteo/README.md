# open_meteo

Snippets built on the [Open-Meteo](https://open-meteo.com/) weather API.
**No API key required** — the free tier allows 10,000 calls/day, 5,000/hour and
600/minute for non-commercial use. Requests are billed fractionally: more than 10
weather variables counts as more than one call, so one `milkyway.py` run (10
variables × 4 models) bills as a few calls.

## `open-meteo.py`

A minimal demonstration of one API call. Prints the **exact JSON Open-Meteo
returned**, with a single key added — `get_para`, the full request URL.

```bash
uv run open-meteo.py                                   # defaults (Taipei, 7 days)
uv run open-meteo.py 24.1375,121.2745                  # set the location
uv run open-meteo.py 24.1375,121.2745 forecast_hours=24 # override any query param
uv run open-meteo.py models= hourly=cloud_cover        # empty value drops a param
```

With no arguments it submits the same request `milkyway.py` makes. A bare
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
  "get_para": "https://api.open-meteo.com/v1/forecast?latitude=25.033&longitude=121.565&hourly=cloud_cover,cloud_cover_low,...&models=ecmwf_ifs025,gfs_global,jma_gsm,icon_global&timezone=auto&forecast_days=7"
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

A browser port of `open-meteo.py` — the demo page published by Pages (see the
root [`README.md`](../README.md#demo-pages)). Input boxes stand in for the
command-line arguments (location, `forecast_days`, `timezone`, `hourly`,
`models`, plus a free-form `key=value` box); submitting fetches and re-renders
the result below, showing the same one-line request summary the script prints to
stderr, the request URL as a clickable link, and the pretty-printed JSON.

`index.html` is just the list page for this folder — one link per demo, reached
from the root hub. Each demo page is named after the script it ports, so a new
demo means a new `<script-name>.html` plus a row on `index.html`.

Open it locally with any static server (`python3 -m http.server`, then
<http://localhost:8000/open_meteo/>) or just open the file directly — it has no
build step and no dependencies.

## `open-meteo_readable.html`

The **same request** as `open-meteo.html` — same form fields, the request core is
copied verbatim — but the response is drawn as an hour-by-hour forecast grid
instead of raw JSON. The raw JSON and the request URL are still there, in a
collapsed `raw JSON & request URL` panel at the bottom.

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
  高雲 → 中雲 → 低雲 (top of the atmosphere downwards); `open-meteo.py` and
  `open-meteo.html` list them low → high. Same ten variables, different listing
  order — reorder the `hourly` box to reorder the grid.
- **Sun and moon rows** (`太陽`, `月亮`, `月相`) sit above the weather rows, their
  second line set in italics because they are not fetched: Open-Meteo offers only
  sunrise/sunset and `daily=moon_phase`. The Meeus low-precision series from
  `milkyway.py` are ported to JavaScript here and agree with the Python to four
  decimal places. They depend on place and time alone, so they are identical on
  every model tab. Solar altitude also decides day vs night for the 天氣 icons,
  which is why the glyphs flip to a moon exactly at sunset.
- **Colour is per variable**, green (good) to red (bad) on a per-variable range;
  a variable with no defined range is left uncoloured rather than tinted on a
  wrong scale.
- **Values a model does not publish show as `-`.** Only `gfs_global` returns
  `visibility` — the other three default models give a row of dashes — and
  `precipitation_probability` is null for `jma_gsm`. A model that does not
  publish a variable also reports the literal string `"undefined"` as its unit,
  which the page suppresses.
- **能見度 is ground-level viewing distance in metres**, derived by Open-Meteo
  from low cloud, humidity and aerosols rather than measured. It saturates at
  24140 m (15 miles, the unit gfs reports it in), so the row is mostly flat and
  dips when moisture builds. It says nothing about upper-air transparency: a
  night can read 24140 and still be overcast at 8 km, which is what the 雲量
  rows are for.
- **`daily=sunrise,sunset,moon_phase` is prefilled** in the extra-params box —
  the only sun/moon figures Open-Meteo has, kept next to the page's own
  calculations as a cross-check. It lives in that box rather than in the default
  parameters so the request core stays identical to `open-meteo.py`. Note the
  daily keys take the **same model suffixing as hourly ones**, so the four
  default models return twelve series, and since these are pure astronomy every
  model returns the identical `moon_phase` and sunrise/sunset within a minute.
  Only the raw JSON panel shows them; the grid renders `hourly` alone. Clear the
  box to drop the parameter.
- **從現在開始** drops the already-past hours — `forecast_days` starts the series
  at 00:00 local, the same trim `score_hours()` does in `milkyway.py`. Untick it
  to see the whole window. Local "now" comes from `utc_offset_seconds`.

It talks to Open-Meteo **straight from the browser**; Pages is static hosting and
cannot run the Python. That works only because Open-Meteo needs no API key (a key
would be visible in page source) and serves `access-control-allow-origin: *`.

Being a parallel implementation, it mirrors the script's behaviour: the same
defaults, the same literal-comma URL construction (`encodeURIComponent` with
`%2C` restored, matching `urlencode(params, safe=",")` byte for byte), the same
added `get_para` key, and the same policy of *displaying* an API error body
rather than throwing. Change one and mirror it in the other.

## `milkyway.py`

Answers "is this time suitable for Milky Way astrophotography?" for a GPS
location, scoring every hour of the next N days from 0–100%.

```bash
uv run milkyway.py                       # Taipei (default)
uv run milkyway.py 24.1375,121.2745      # 武嶺 / 合歡山, 7 days
uv run milkyway.py 24.1375,121.2745 3    # 3 days
```

Input is `lat,lon` as `argv[1]`; `argv[2]` is the number of forecast days
(default 7, max 16). The timezone is resolved from the coordinates by the API
(`timezone=auto`), so it works anywhere, not just Taiwan.

### Output

First a summary row per night, showing that night's best hour:

```
各夜最佳時段
  夜晚        最佳   機率 信心 月相        銀心 雲量 總(低/中/高)    降雨
  08/18(二)   23:00   22% 低   眉月36%      20° 36 (22/5/7)           59%

最佳時刻 08/18(二) 23:00 機率 22% (信心 低) — 機會不大
```

Then a full **24-hour grid for every forecast day**, one column per hour, in the
layout stargazing apps use (abbreviated here — the real output is all 24 hours):

```
08/17(一) 逐時
時間      16   17   18   19   20   21   22   23
                              ·    ·    ·    ·
機率      0%   0%   0%   0%   9%  11%  13%  12%
信心       -    -    -    -   中   中   低   低
銀心     12°  22°  30°  35°  37°  35°  29°  21°
月亮     53°  47°  38°  27°  15°   3°   落   落
太陽     32°  18°   5°  -8° -21° -33° -43° -50°
雲量      54   54   42   33   35   40   48   54
高雲      17   14   12   11   10    9    9   11
中雲      12    7    8   10   20   24   26   26
低雲      44   48   38   31   29   28   31   30
降雨     43%  50%  59%  67%  69%  72%  69%  64%
露點差   2.4  2.3  2.2  2.1  2.2  2.2  2.2  2.2
ecmwf      0    0    0    0   14   15   14   10
gfs        0    0    0    0   17   23   34   30
jma        0    0    0    0    1    2    3    5
icon       0    0    0    0    4    2    3    4
```

Daylight hours are included so the weather series is continuous, but they score
0 — the astronomy gates shut them, which the `太陽` and `銀心` rows explain. A
`·` under the hour marks the hours that clear those gates, i.e. the only ones
where the score means anything. Today's grid starts at the current hour rather
than 00:00.

The `月亮` / `太陽` / `銀心` rows are altitude in degrees; `落` means the moon is
below the horizon and out of the way.

**`0` and `<1` mean different things.** A hard `0` is structural — the sun is
up, or the core is below the horizon, or a model is forecasting 100% low cloud,
and no arrangement of the other terms can lift it. `<1` is a dark hour with the
core up whose score is real but under 0.5%, typically a bright gibbous moon
multiplied by heavy overcast (`moon_free` ≈ 0.2 × `sky_quality` ≈ 0.01 ≈ 0.2%).
Both are hopeless in practice; only the first is impossible in principle.

The four bottom rows are each model's own score for that hour, and they are the
point of the multi-model query. On one of the nights above, `gfs` and `icon` saw
a usable 22:00–23:00 window (29–45) that `ecmwf` and `jma` flatly rejected
(2–7) — a four-way split on identical astronomy, which is exactly why those
hours read `信心 低` despite being the night's best. Averaged into one number,
that disagreement would have vanished.

Note the two views group differently on purpose: the summary is by **night**
(hours after midnight belong to the evening they started, so a 01:00 shot is
filed under the previous date), while the grid is by **calendar day**, since a
continuous 24-hour weather series is what makes it comparable to an app's
hourly table.

The 24-column grid is about 127 characters wide, so it wants a reasonably wide
terminal. Pass a smaller day count (`uv run milkyway.py <lat,lon> 2`) to keep
the output short.

### How the score works

```
score = darkness × core_up × moon_free × sky_quality
```

The first three are **astronomy gates** — any of them can zero the hour, and no
weather forecast can rescue it. They are computed locally (Meeus low-precision
solar/lunar series), because Open-Meteo has no astronomy beyond sunrise/sunset
and `daily=moon_phase`:

| Term | Basis |
| --- | --- |
| `darkness` | Sun altitude: 0 above −12°, ramping to 1 at −18° (astronomical night) |
| `core_up` | Galactic core altitude: 0 below the horizon, ramping to 1 by 25° — near the horizon the core is buried in airmass and ground light |
| `moon_free` | 0 impact when the moon is below −8°; otherwise scales with illuminated fraction and altitude, slightly relaxed when the moon is far from the core |

`sky_quality` is the **weather** term, from the forecast. Cloud layers are
treated as independent screens — low cloud blocks completely, mid cloud nearly
so, and high cirrus still robs the core of contrast, so it carries real weight
(0.70) rather than being shrugged off. Reported total cover acts only as a
discounted floor, so an optimistic layer breakdown cannot talk the score up.
Also folded in: precipitation probability, temperature–dew-point spread (a small
spread means fog, haze and dew on the front element — the classic ruined
session), relative humidity above 85%, visibility, and wind (strong wind shakes
a tripod through a long exposure; dead calm with saturated air is how valleys
fog in).

### The four models

`sky_quality` is computed **separately for each of the four models** and then
averaged — the per-model scores are the bottom rows of the hourly grid. These
are four completely separate forecasting systems, each run by a different
national or intergovernmental weather agency, not four views of one dataset:

| id | Agency | Country | Global resolution | New run |
| --- | --- | --- | --- | --- |
| `ecmwf_ifs025` | ECMWF (European Centre for Medium-Range Weather Forecasts) | EU / intergovernmental | 0.25° ≈ 25 km | every 6 h |
| `gfs_global` | NOAA / NCEP — Global Forecast System | USA | ~11–25 km | every 1 h |
| `jma_gsm` | JMA — Global Spectral Model | Japan | ~20 km | every 3 h |
| `icon_global` | DWD (Deutscher Wetterdienst) | Germany | ~11 km | every 3 h |

Open-Meteo's docs list each model *family*, so its quoted resolution ranges fold
in high-resolution regional nests (HRRR for GFS, ICON-D2 for ICON) that only
cover the US and Europe. The `_global` variants are used here precisely because
the regional nests do not cover Taiwan.

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
- **JMA GSM** has home-field advantage for East Asia and typhoons.
- **GFS** is the freshest, updating hourly, and the most permissively open.

The script averages all four with **equal weight**, treating them as peers.
Given ECMWF's track record, weighting it higher would arguably be more accurate;
equal weighting is kept because unequal weights are hard to justify without
verifying against actual outcomes. It is a one-line change in `score_hours()`.

Note this is a **multi-model** ensemble — four models, one run each — not a
single-model ensemble, where one model runs 30–50 times with perturbed initial
conditions. Open-Meteo exposes those separately via its Ensemble API
(`ensemble-api.open-meteo.com`), which would allow a true "X% of members show
clear sky" probability instead of the constructed score used here.

### Confidence

`信心` (高/中/低) is deliberately a **separate axis** from the score. It is
eroded by two things: the spread of the per-model scores, and forecast lead time
— a unanimous 90% six days out is still a guess.

### Notes and caveats

- Not every model publishes every variable: of the four models only
  `gfs_global` returns `visibility` (`ecmwf_ifs025`, `jma_gsm` and
  `icon_global` are all null), and `precipitation_probability` is null for
  `jma_gsm`. Missing values fall back to the ensemble mean, so one model's
  silence never makes it look artificially clear — though for `visibility` that
  mean is gfs on its own.
- **`MODELS` needs at least two entries.** Open-Meteo only suffixes variable
  names with the model (`cloud_cover_gfs_global`) when several models are
  requested; ask for one and the keys come back bare as `cloud_cover`. Left
  unchecked that degrades silently — every variable reads as `None`, every
  fallback is neutral, and the script reports a perfect sky at every hour — so
  `fetch_forecast()` validates the response shape and exits instead.
- Requesting `&models=…` snaps the coordinate to the model grid, so the echoed
  lat/lon and elevation may differ slightly from the input.
- The score says nothing about **light pollution** — it is a sky-conditions
  score, not a darkness-of-site score. Taipei and a 3,000 m ridge with identical
  weather score identically. Pick the site yourself.
- Galactic core coordinates are J2000 (RA 17h45m40.04s, Dec −29°00′28″).
  Precession since then is well under a degree — far below the accuracy of the
  low-precision moon series — so they are used as-is.
- Moon output was cross-checked against Open-Meteo's own `daily=moon_phase`
  field, which the script does not otherwise use.
