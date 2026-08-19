# code_snippet_life

A collection of small, self-contained code snippets. Each snippet lives in its own folder with its own `README.md` describing what it does and how to run it.

**Live demo:** https://jiechau.github.io/code_snippet_life/index.html

## Snippets

| Snippet | Description |
| --- | --- |
| [google_news_url/](google_news_url/README.md) | Resolve a Google News redirect URL (e.g. from an RSS feed) to its real destination URL. Python and Node implementations. |
| [cwa_opendata/](cwa_opendata/README.md) | Query Taiwan CWA Open Data for daily sunrise/sunset (`cwa_sunrise.py`) and moonrise/moonset (`cwa_moonrise.py`) times per county. |
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
holds the saved stargazing spots (三總, 瑞光路, 大崙頭山, 大武崙砲台, 烏石港, 東澳,
石梯坪, 柚子湖, 龍磐公園, 暗空公園) that fill the location buttons, plus the default coordinates taken from the
first of them. Each page loads it as `../places.js`, so adding or reordering a spot is
a one-line change in one file rather than the same edit made eight times. It is the
only file shared across snippet folders.

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
| [astro_score/astro-score_readable.html](astro_score/astro-score_readable.html) | That grid cut down to what stargazing needs: one model, the cloud decks plus 降雨/氣溫, locally computed 太陽/月亮/月相/銀心 rows (the last being the Milky Way core's altitude, shown but not scored, with a 銀心 (max) row under it giving the fixed ceiling `90° − |緯度 + 29°|` that latitude allows), the site's light pollution as 光害 (SQM) / Bortle / LP Zone from [David Lorenz's World Atlas](https://djlorenz.github.io/astronomy/lp/) — the one keyless, CORS-enabled light-pollution source, read straight out of its gzipped binary tiles with `DecompressionStream`, the place the coordinates fall in (中華民國/宜蘭縣/南澳鄉/蘇澳鎮, via BigDataCloud's keyless reverse geocoder), and a 觀星 score per hour — `(100 − 雲量) × (100 − 月亮扣分) / 100`, zeroed while the sun is above −10°, where 月亮扣分 ramps 0 → 100 as the moon climbs 0° → 10°. An extra-params box prefilled `past_days=7` extends the grid backwards, visible once 從現在開始 is unticked. Loosely after `astro_score/milkyway.py`. |
| [astro_score/astro-score_daily.html](astro_score/astro-score_daily.html) | The same 觀星 score, one week at a glance: a row per saved spot, a column per day, and each cell two block glyphs `▂▄▆█` — one per half-day (00–11, 12–23), sized by the **best** 觀星 hour in it (>90 `█`, >70 `▆`, >50 `▄`, >30 `▂`, at or below 30 blank). A night straddles midnight, so it reads across two cells: one day's right glyph beside the next day's left one. One request per saved place instead of one for a location box (pooled 4 at a time, since Open-Meteo 429s a burst), each returning all four forecast models; tabs pick which model the bars are scored from, defaulting to `jma_seamless` for its ~5 km nest over Taiwan. An extra-params box prefilled `past_days=7` adds the week just gone as columns left of today, hidden until 從今天開始 (hide past days) is unticked. |
| [pure_math/galactic_center.html](pure_math/galactic_center.html) | The `銀心` row of `astro-score_readable`, on its own: a local time and a `lat,lon` in, the Milky Way core's altitude and azimuth out, with Julian Day, GMST, local sidereal time and hour angle all printed on the way. Sagittarius A* is a fixed equatorial position, so this needs no ephemeris — and it shows the `銀心 (max)` ceiling `90° − |φ − δ|` beside the live value. **No API call.** |
| [pure_math/sun_phase.html](pure_math/sun_phase.html) | The `太陽` row on its own — Meeus' two-term solar series from mean longitude through the centre correction to altitude and azimuth, ending in the `DARK_SUN_ALT` (−10°) verdict that zeroes an hour's 觀星 score. Names the conventional twilight bands for context. **No API call.** |
| [pure_math/moon_phase.html](pure_math/moon_phase.html) | The `月亮` and `月相` rows on their own — the five fundamental arguments, then 14 longitude / 8 latitude / 4 distance terms, then altitude, then the illuminated fraction from the moon–sun elongation, and the Chinese phase name (`moon_phase_name()` ported from `milkyway.py`). Ends with the 月亮扣分 ramp `MOON_KILL_ALT` drives. **No API call.** |
| [bigdatacloud/reverse-geocode.html](bigdatacloud/reverse-geocode.html) | BigDataCloud's keyless `reverse-geocode-client` endpoint — a `lat,lon` in, the raw JSON of place names out, plus `countryName/principalSubdivision/city/locality` joined into the one line `astro_score` keeps from it. Same page as `open-meteo.html` with the form cut to a single input. |
| [light_pollution/binary-tile.html](light_pollution/binary-tile.html) | One tile of [David Lorenz's World Atlas](https://djlorenz.github.io/astronomy/lp/), fetched and decoded in the browser: a `lat,lon` and an atlas year in; **SQM**, **Bortle** and **LP Zone** out, with every intermediate and the raw bytes shown. The file holds neither SQM nor Bortle — just one quantised integer per 30-arcsec grid point, delta-encoded — so the page is mostly the decode. Year buttons re-read the same point from 2016–2025, which turns the atlas into a trend. Same code as the `光害` rows of `astro-score_readable.html`. |
| [google_news_url/google_new_url.html](google_news_url/google_new_url.html) | `google_news_url/google_new_url.py` — search the Google News RSS feed for a keyword, sort by `<pubDate>`, and resolve the newest N redirect links to real article URLs. **Requires a CORS proxy** (picked in the page). |

Pages hosting is **static**, so a demo page cannot run the Python; it re-implements
the snippet in JavaScript and calls the upstream API directly from the browser.
`pure_math/` sidesteps that entirely — it calls no API, so a static host is all it
ever needed.
That is straightforward for a keyless, CORS-enabled API like Open-Meteo or
BigDataCloud's `-client` endpoints. A snippet needing a credential (`cwa_opendata`)
has no demo, because the key would be readable in page source. `google_news_url` scrapes `news.google.com`, which sends no
`Access-Control-Allow-Origin` at all, so its page routes every request through a
user-selected public CORS proxy — that works, but those proxies are flaky and
rate-limited, so expect some rows to fail. Where a page and a script are two
implementations of the same snippet, changing one means mirroring the other.

Preview locally with any static server:

```bash
python3 -m http.server   # then open http://localhost:8000/
```
