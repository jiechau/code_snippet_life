# code_snippet_life

A collection of small, self-contained code snippets. Each snippet lives in its own folder with its own `README.md` describing what it does and how to run it.

**Live demo:** https://jiechau.github.io/code_snippet_life/index.html

## Snippets

| Snippet | Description |
| --- | --- |
| [google_news_url/](google_news_url/README.md) | Resolve a Google News redirect URL (e.g. from an RSS feed) to its real destination URL. Python and Node implementations. |
| [cwa_opendata/](cwa_opendata/README.md) | Query Taiwan CWA Open Data for daily sunrise/sunset (`cwa_sunrise.py`) and moonrise/moonset (`cwa_moonrise.py`) times per county. The only snippet needing an **API key** — free, and on the demo pages a box on the form. |
| [open_meteo/](open_meteo/README.md) | Open-Meteo weather API (no key needed): a raw one-call demo returning the exact JSON plus the request URL (`open-meteo.py`). |
| [astro_score/](astro_score/README.md) | Score how good each upcoming hour is for stargazing and Milky Way astrophotography at a GPS location (`milkyway.py`) — Open-Meteo cloud forecasts combined with locally computed sun, moon and galactic-core geometry. |
| [pure_math/](pure_math/README.md) | The astronomy behind `astro_score/`, one formula per page: galactic-core altitude, solar altitude, lunar altitude and phase. Demo pages only — no script and **no API call**, just numbers in and numbers out. |
| [light_pollution/](light_pollution/README.md) | How dark is the sky at a `lat,lon`? Decodes a tile of David Lorenz's World Atlas of Artificial Night Sky Brightness to SQM, Bortle and LP Zone. Demo page only — the tiles are static files, so there is no script and no key. |
| [bigdatacloud/](bigdatacloud/README.md) | Reverse-geocode a `lat,lon` to place names with BigDataCloud (no key needed). Demo page only — the call is one keyless `GET`, so there is no script. |

## Demo pages

Some snippets have a browser demo. Pushing to `main` publishes the repo as a
static site to both hosts:

| Host | Config | URL |
| --- | --- | --- |
| GitHub Pages | [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) | https://jiechau.github.io/code_snippet_life/index.html |
| GitLab Pages | [`.gitlab-ci.yml`](.gitlab-ci.yml) | https://jiechau.gitlab.io/code_snippet_life/index.html |

The GitLab URL has Pages access control on, so it redirects to a GitLab login
rather than serving anonymously. `origin` also pushes to Bitbucket, which offers
no Pages hosting — it is a mirror only.

One file is shared by every demo page: [`places.js`](places.js) at the repo root
holds the saved stargazing spots (瑞光路, 大武崙砲台, 內洞停車場, 烏石港,
東澳, 石梯坪, 加路蘭, 龍磐公園, 合歡山, 柚子湖) that fill the location buttons, plus the
default coordinates taken from the first entry. Each page loads it as
`../places.js`, so adding or reordering a spot is a one-line change in one file
rather than the same edit made nine times. It is the only file shared across
snippet folders. The two `cwa_opendata/` pages are the exception that does not
load it: that API is addressed by **county**, not by `lat,lon`, so they offer the
22 county names instead.

That first entry is not a saved spot: **輸入** is wherever you are asking about
right now — what each page's location box writes back to, and what its
**使用目前位置 (use current position)** button points at the device's own GPS.
Keeping it in the shared list rather than in a page is what lets
[astro-score_daily.html](astro_score/astro-score_daily.html) join in: its rows *are*
the places, so 輸入 is a row and its box edits that one row rather than choosing the
place. Geolocation needs
a secure context, so it works on the published `https://` pages and on `localhost`
but not on `file://`; a refusal is printed beside the button and nothing is stored,
so a reload is back to the coordinate the file was written with.

Pages are two levels of list: the root [`index.html`](index.html) links to one
`<snippet>/index.html` per snippet folder, and that folder list links to one page
per demo, each named after the script it ports.
Both `astro_score/astro-score_*.html` pages are an exception: they are re-scoped
forks of `open_meteo/open-meteo_readable.html` rather than ports of one script, so
they take the folder's name. `bigdatacloud/` and `pure_math/` hold no script at
all, so their pages are named after what they compute instead — the endpoint
called (`reverse-geocode-client` → `reverse-geocode.html`), or the quantity
produced (`galactic_center.html`).

| Page | Demo of |
| --- | --- |
| [open_meteo/open-meteo.html](open_meteo/open-meteo.html) | `open_meteo/open-meteo.py` — fill in the arguments, submit, see the request URL and the returned JSON. |
| [open_meteo/open-meteo_readable.html](open_meteo/open-meteo_readable.html) | The same request, drawn as an hour-by-hour forecast grid: a tab per model, a row per variable, colour-coded and scrollable. Both pages in this folder are deliberately **API-only** — every row is a series Open-Meteo returned, with no place-name lookup and no locally computed astronomy. |
| [astro_score/astro-score_readable.html](astro_score/astro-score_readable.html) | That grid cut down to what stargazing needs: the cloud decks plus 降雨/氣溫 (all four models fetched together, 雲量來源 tabs picking which one the grid is drawn from and 觀星 scored with, defaulting to `icon_global`), locally computed 太陽/月亮/月相/銀心 rows (the last being the Milky Way core's altitude, shown but not scored, with a 銀心 (max) row under it giving the fixed ceiling `90° − |緯度 + 29°|` that latitude allows), the site's light pollution as 光害 (SQM) / Bortle / LP Zone from [David Lorenz's World Atlas](https://djlorenz.github.io/astronomy/lp/) — the one keyless, CORS-enabled light-pollution source, read straight out of its gzipped binary tiles with `DecompressionStream`, the place the coordinates fall in (中華民國/宜蘭縣/南澳鄉/蘇澳鎮, via BigDataCloud's keyless reverse geocoder), and a 觀星 score per hour — `(100 − 雲量) × (100 − 月亮扣分) / 100`, zeroed while the sun is above −10°, where 月亮扣分 ramps 0 → 100 as the moon climbs 0° → 10°. An extra-params box prefilled `past_days=7` extends the grid backwards, visible once 從現在開始 is unticked. Loosely after `astro_score/milkyway.py`. |
| [astro_score/astro-score_daily.html](astro_score/astro-score_daily.html) | The same 觀星 score, one week at a glance: a row per place, a column per day, and each cell two block glyphs `▂▄▆█` — one per half-day (00–11, 12–23), sized by the **best** 觀星 hour in it (>90 `█`, >70 `▆`, >50 `▄`, >30 `▂`, at or below 30 blank) — each over a purple `▀` strip shaded by the block's best **MilkyScore**, `銀心 altitude° × 觀星/100` (>50, >40, >30, >20, blank at or below 20), which colours only when the sky is good *and* the galactic core is up. A night straddles midnight, so it reads across two cells: one day's right glyph beside the next day's left one. The first row is 輸入, the `places.js` entry that is not a saved spot: a `lat,lon` box above Fetch and a 📍 使用目前位置 button move that one row, while the saved spots stay as the file has them; a second meta line names it (`輸入: 中華民國/新北市/烏來區`) from the same keyless BigDataCloud lookup the readable page uses. One request per place instead of one for a location box (pooled 4 at a time, since Open-Meteo 429s a burst), each returning all four forecast models; tabs pick which model the bars are scored from, defaulting to `icon_global` (`jma_seamless`, with its ~5 km nest over Taiwan, is one click away). An extra-params box prefilled `past_days=7` adds the week just gone as columns left of today, shown by default — 從今天開始 (hide past days) starts unticked here, so the forecast opens beside what the sky actually did. |
| [pure_math/galactic_center.html](pure_math/galactic_center.html) | The `銀心` row of `astro-score_readable`, on its own: a local time and a `lat,lon` in, the Milky Way core's altitude and azimuth out, with Julian Day, GMST, local sidereal time and hour angle all printed on the way. Sagittarius A* is a fixed equatorial position, so this needs no ephemeris — and it shows the `銀心 (max)` ceiling `90° − |φ − δ|` beside the live value. **No API call.** |
| [pure_math/sun_phase.html](pure_math/sun_phase.html) | The `太陽` row on its own — Meeus' two-term solar series from mean longitude through the centre correction to altitude and azimuth, ending in the `DARK_SUN_ALT` (−10°) verdict that zeroes an hour's 觀星 score. Names the conventional twilight bands for context. **No API call.** |
| [pure_math/moon_phase.html](pure_math/moon_phase.html) | The `月亮` and `月相` rows on their own — the five fundamental arguments, then 14 longitude / 8 latitude / 4 distance terms, then altitude, then the illuminated fraction from the moon–sun elongation, and the Chinese phase name (`moon_phase_name()` ported from `milkyway.py`). Ends with the 月亮扣分 ramp `MOON_KILL_ALT` drives. **No API call.** |
| [bigdatacloud/reverse-geocode.html](bigdatacloud/reverse-geocode.html) | BigDataCloud's keyless `reverse-geocode-client` endpoint — a `lat,lon` in, the raw JSON of place names out, plus `countryName/principalSubdivision/city/locality` joined into the one line `astro_score` keeps from it. Same page as `open-meteo.html` with the form cut to a single input. |
| [light_pollution/binary-tile.html](light_pollution/binary-tile.html) | One tile of [David Lorenz's World Atlas](https://djlorenz.github.io/astronomy/lp/), fetched and decoded in the browser: a `lat,lon` and an atlas year in; **SQM**, **Bortle** and **LP Zone** out, with every intermediate and the raw bytes shown. The file holds neither SQM nor Bortle — just one quantised integer per 30-arcsec grid point, delta-encoded — so the page is mostly the decode. Year buttons re-read the same point from 2016–2025, which turns the atlas into a trend. Same code as the `光害` rows of `astro-score_readable.html`. |
| [cwa_opendata/cwa_sunrise.html](cwa_opendata/cwa_sunrise.html) | `cwa_opendata/cwa_sunrise.py` — a county and a date in, Taiwan CWA's own sunrise / transit / sunset times and azimuths out, plus the length of the day, formatted exactly as the script prints it. **Needs a free API key**, which is a box on the form: a static page has no `CWA_API_KEY` and no `config.yml` to read, and nothing is stored, so it is typed per visit. |
| [cwa_opendata/cwa_moonrise.html](cwa_opendata/cwa_moonrise.html) | `cwa_opendata/cwa_moonrise.py` — the same, for the moon, which does not keep to a calendar day: it rises ~50 min later each time, so rise, transit and set are fetched over a **three-day** window and stitched into the one cycle that starts on the day you asked for, with borrowed times tagged 昨 or 明. The three records are laid out under the answer with the cells the stitching took highlighted, and a line names which of the six branches fired. Same API-key box. |
| [google_news_url/google_new_url.html](google_news_url/google_new_url.html) | `google_news_url/google_new_url.py` — search the Google News RSS feed for a keyword, sort by `<pubDate>`, and resolve the newest N redirect links to real article URLs. **Requires a CORS proxy** (picked in the page). |

Pages hosting is **static**, so a demo page cannot run the Python; it re-implements
the snippet in JavaScript and calls the upstream API directly from the browser.
`pure_math/` sidesteps that entirely — it calls no API, so a static host is all it
ever needed.
That is straightforward for a keyless, CORS-enabled API like Open-Meteo or
BigDataCloud's `-client` endpoints. `cwa_opendata` needs a credential, which a
static page cannot hold — there is no environment variable to read, and a key in
the source would be public the moment it is published — so its two pages ask for
one in a **form field** instead: masked in the displayed URL, sent only to
`opendata.cwa.gov.tw`, and kept between visits in this browser's `localStorage`
only if you tick **記住金鑰**, which is off by default. (CWA's successful responses
send `Access-Control-Allow-Origin: *`; its 401 does not, so a wrong key reaches the
browser as a blocked request rather than a readable status, and both pages say so.)
`google_news_url` scrapes `news.google.com`, which sends no
`Access-Control-Allow-Origin` at all, so its page routes every request through a
user-selected public CORS proxy — that works, but those proxies are flaky and
rate-limited, so expect some rows to fail. Where a page and a script are two
implementations of the same snippet, changing one means mirroring the other.

Preview locally with any static server:

```bash
python3 -m http.server   # then open http://localhost:8000/
```
