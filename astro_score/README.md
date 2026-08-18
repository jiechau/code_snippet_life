# astro_score

Scoring the sky for stargazing and Milky Way astrophotography: given a `lat,lon`,
how good is each upcoming hour? Weather comes from the
[Open-Meteo](https://open-meteo.com/) API, the astronomy is computed locally.
**No API key required** — the free tier allows 10,000 calls/day, 5,000/hour and
600/minute for non-commercial use. Requests are billed fractionally: more than 10
weather variables counts as more than one call, so one `milkyway.py` run (10
variables × 4 models) bills as a few calls.

The plain, unscored API demo this folder grew out of lives next door in
[`open_meteo/`](../open_meteo/README.md).

**API reference: <https://open-meteo.com/en/docs>** — every variable name used in
`hourly=` / `daily=`, the model ids for `models=` and the units each field comes
back in. This folder's page fixes its own variables and model, so the docs matter
here mainly when changing those constants; the adjustable form is
[`open_meteo/`](../open_meteo/README.md)'s.

**Live demo:** https://jiechau.github.io/code_snippet_life/astro_score/

- [AstroScore readable](https://jiechau.github.io/code_snippet_life/astro_score/astro-score_readable.html)
  — an hour-by-hour grid with a 觀星 score per hour.

## The four models

`milkyway.py` queries all four models below and averages them.
`astro-score_readable.html` deliberately does not: it asks for `icon_global`
alone. The same four-id list is also sent by everything in
[`open_meteo/`](../open_meteo/README.md), so keep it in step across both folders.
These are four
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

### Weighting (`milkyway.py`)

`sky_quality` is computed **separately for each of the four models** and then
averaged — the per-model scores are the bottom rows of the hourly grid. The
script averages all four with **equal weight**, treating them as peers.
Given ECMWF's track record, weighting it higher would arguably be more accurate;
equal weighting is kept because unequal weights are hard to justify without
verifying against actual outcomes. It is a one-line change in `score_hours()`.

Note this is a **multi-model** ensemble — four models, one run each — not a
single-model ensemble, where one model runs 30–50 times with perturbed initial
conditions. Open-Meteo exposes those separately via its Ensemble API
(`ensemble-api.open-meteo.com`), which would allow a true "X% of members show
clear sky" probability instead of the constructed score used here.

## `astro-score_readable.html`

The only demo page in this folder, listed as **AstroScore readable**. One
question: **which hours are worth going out for.** It is the
[`open_meteo/open-meteo_readable.html`](../open_meteo/README.md#open-meteo_readablehtml)
grid — same layout, same colouring, same 從現在開始 trim, same saved spots, same
collapsed raw JSON panel, same place name on the meta line
([The place name](#the-place-name)) — with a 觀星 score added and everything that
does not feed it removed.

- **The form is two fields and a location.** `hourly`, `models` and `extra
  params` are gone, fixed as constants in the page, because there is exactly one
  request worth making here. Only `forecast_days`, `timezone` and the place
  remain. `buildUrl()` / `fetchForecast()` / `paramsFromForm()` are still the
  byte-for-byte port of `open_meteo/open-meteo.py`; only the constants they are
  fed differ.
- **One model, no tabs.** `models=icon_global` alone, so the score has a single
  unambiguous 雲量 instead of four to reconcile. A single model makes Open-Meteo
  return **bare** series keys (`cloud_cover`, not `cloud_cover_icon_global`),
  which `seriesKey()` already handles.
- **Six variables, not ten.** The cloud decks plus 降雨 and 氣溫 —
  能見度/濕度/露點/風速 are dropped, along with the `daily=` and `past_days=`
  extras. 降雨 and 氣溫 are not score inputs (`astroScore()` reads `cloud_cover`
  alone); they are on screen to be read by eye when picking a night out. A 7-day
  response is about **7.0 KB / 168 hours**, versus ~64 KB / 336 hours on
  `open_meteo/open-meteo_readable.html`.
- **A row per variable**, labelled in Chinese with the unit and an abbreviated
  API name underneath. The label column is frozen while the hours scroll, so its
  width costs a column of forecast at every scroll position — keep new labels to
  two or three CJK characters. The unabbreviated name is on the cell's `title`.
- **Sun and moon rows** (`太陽`, `月亮`, `月相`) sit above the weather rows, set
  in italics because they are not fetched: Open-Meteo offers only sunrise/sunset
  and `daily=moon_phase`, neither of which is an hourly altitude. The Meeus
  low-precision series from `milkyway.py` are ported to JavaScript here and agree
  with the Python to four decimal places. **This is the only page that has them** —
  `open_meteo/open-meteo_readable.html` used to carry a copy and no longer does, so
  the JavaScript port and `milkyway.py` are now the only two implementations to keep
  in step. Solar altitude also decides day vs night for the 天氣 icons, which is why
  the glyphs flip to a moon exactly at sunset, and it is what the 觀星 score gates on.
- **從現在開始** drops the already-past hours — `forecast_days` starts the series
  at 00:00 local, the same trim `score_hours()` does in `milkyway.py`. Local "now"
  comes from `utc_offset_seconds`.
- **The 觀星 row** sits directly under 時間, above 天氣, its label in green. Cells
  are tinted on the usual scale, inverted — 100 is green.

It talks to Open-Meteo **straight from the browser**; Pages is static hosting and
cannot run the Python. That works only because Open-Meteo needs no API key (a key
would be visible in page source) and serves `access-control-allow-origin: *`.

### The place name

The page names the place the coordinates fall in, so a bare `24.5145,121.8277`
reads as somewhere. It goes on a **second line** under the request summary:

```
HTTP 200  application/json; charset=utf-8  5743 bytes  0.41s  — Asia/Taipei (GMT+8), 24.625°, 121.75°, 37 m
中華民國/宜蘭縣/南澳鄉/蘇澳鎮
```

It is a second API — [BigDataCloud](https://www.bigdatacloud.com/)'s
`reverse-geocode-client` endpoint — chosen for the same two reasons Open-Meteo
is usable here: **no key** and `access-control-allow-origin: *`, so it works
from static hosting. One request per fetch, `localityLanguage=zh`, and the four
fields `countryName` / `principalSubdivision` / `city` / `locality` joined with
`/`. Points at sea return a country-less answer (`0,0` is just 大西洋) and the
last two fields sometimes repeat each other (臺北市 as both), so empty and
duplicate parts are dropped.

Two things worth knowing:

- **The coordinates sent are the requested ones, not the response's.**
  Open-Meteo snaps to its model grid, and the gap matters at this zoom level:
  東澳 (24.5145, 121.8277) is 南澳鄉/蘇澳鎮, while the 24.625, 121.75 grid point
  the forecast came back on is 冬山鄉 — a different township ~6 km away. The
  meta line therefore prints the grid point as coordinates and the requested
  point as a name.
- **It is a label, never data.** The lookup is fired after the forecast is
  already on screen, and a failure, a timeout or an empty answer simply leaves
  the meta block at one line. It also never overwrites a line a newer fetch has
  since written, so clicking through saved spots cannot leave the wrong name
  attached.

Results are cached per coordinate for the life of the page. `reverseGeocode()` /
`appendPlaceName()` now live **only here** — neither `open_meteo/` page has them,
because those two deliberately show nothing Open-Meteo did not return. So this is
no longer a duplicated block to keep in step; it is this page's own.

### The location field

The location box sits **last in the form, directly above Fetch**, out of normal
parameter order on purpose: it is the only field normally touched, so it belongs
next to the button. A narrow `lat,lon` box with the saved spots beside it: 三總,
瑞光路, 大崙頭山, 大武崙砲台, 東澳, 烏石港, 暗空公園. Clicking one fills the
coordinates **and refetches** — leaving a stale grid under a new location would
misrepresent it. The pressed button shows which spot is displayed, and a
hand-typed coordinate presses none. They come from the `PLACES` array in
[`../places.js`](../places.js), shared by every demo page in the repo, whose first
entry is also the default location — so adding, removing or reordering a spot is a
one-line change **in that one file**, and it changes what all three pages open on.

`index.html` is just the list page for this folder, reached from the root hub.

Open it locally with any static server (`python3 -m http.server`, then
<http://localhost:8000/astro_score/>) or just open the file directly — it has no
build step and no dependencies.

### The score

Daylight is a hard cutoff, the moon is a ramp, and the rest is just clear sky.
The page states this formula on itself, above the form:

```
觀星     = 0                                        if 太陽 > −10°
月亮扣分 = min(100, max(0, 月亮 / 10 × 100))        0 below the horizon, 100 from +10° up
觀星     = (100 − 雲量) × (100 − 月亮扣分) / 100    otherwise
```

Run on a 20%-cloud hour, the moon term is the whole story:

| 雲量 | 月亮 | 計算 | 觀星 |
| --- | --- | --- | --- |
| 20 | −5° | `(100−20) × (100−0)   / 100` | **80** — moon down, near enough a clear night |
| 20 | +2° | `(100−20) × (100−20)  / 100` | **64** — a low moon costs a fifth, not the hour |
| 20 | +8° | `(100−20) × (100−80)  / 100` | **16** — almost gone |
| 20 | +10° | `(100−20) × (100−100) / 100` | **0** — moon high enough to write the hour off |

The penalty is **altitude only** — a crescent and a full moon at the same height
score the same, which is why 月相 stays on screen as its own row to judge by eye.

Sun and moon altitudes come from the same Meeus series as the 太陽/月亮 rows,
computed in the page. Null cloud cover scores `-`, not 100. The result is
fractional and displayed rounded.

This is **deliberately not** a port of `sky_quality()` below — it is a simpler
rule of thumb kept on purpose, so the two are free to disagree. The astronomy
*is* shared, though: change the Meeus series here, in `milkyway.py` or in
`open_meteo/open-meteo_readable.html` and all three need re-checking.

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

It scores each of the four models separately and averages them — see
[The four models](#the-four-models) above for what they are and
[Weighting](#weighting-milkywaypy) for why they are weighted equally.

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

### Confidence

`信心` (高/中/低) is deliberately a **separate axis** from the score. It is
eroded by two things: the spread of the per-model scores, and forecast lead time
— a unanimous 90% six days out is still a guess.

### Notes and caveats

- Not every model publishes every variable: of the four models only
  `gfs_global` returns `visibility` (`icon_global`, `jma_seamless` and
  `ecmwf_ifs025` are all null), and `precipitation_probability` is null for
  `jma_seamless`. Missing values fall back to the ensemble mean, so one model's
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
