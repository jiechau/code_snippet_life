# light_pollution

How dark is the sky at a `lat,lon`? **No script and no API key** — two pages over
[David Lorenz's World Atlas of Artificial Night Sky Brightness](https://djlorenz.github.io/astronomy/lp/):
[binary-tile.html](binary-tile.html) fetches one tile and decodes it in the browser,
showing every step, and [light_pollution_map.html](light_pollution_map.html) draws the
same atlas as a map you can pan, reading any point you click.

Like [`bigdatacloud/`](../bigdatacloud/README.md), this folder holds no script:
the whole thing is one `GET` for a static file plus about twenty lines of
arithmetic, so a Python version would demonstrate nothing the pages do not.
Neither page is named after a script, because there is none — `binary-tile.html`
takes the name of the file it reads (`binary_tile_<x>_<y>.dat.gz`), for the same
reason `reverse-geocode.html` is named after its endpoint, and
`light_pollution_map.html` is named after what it draws.

**Live demo:** https://jiechau.github.io/code_snippet_life/light_pollution/

- [binary tile](https://jiechau.github.io/code_snippet_life/light_pollution/binary-tile.html)
  — a `lat,lon` and an atlas year in; SQM, Bortle and LP Zone out, with every
  intermediate step and the raw bytes shown.
- [light pollution map](https://jiechau.github.io/code_snippet_life/light_pollution/light_pollution_map.html)
  — the same atlas as a **map**: one layer per atlas year plus the 2013–2025 trend, over
  a choice of basemap, with an opacity slider and the 15-step colour key.
  **Click anywhere and it reads that point** — and the number comes from the *binary*
  tile, not from the colour, so the picture and the figure cannot disagree. Past zoom 8
  the overlay is painted from those binary tiles too, at the atlas's true 30-arcsec
  resolution.

## One point, or the whole view

The two pages are the same atlas asked two ways, and each is bad at the other's job:

| | [binary tile](binary-tile.html) | [light pollution map](light_pollution_map.html) |
| --- | --- | --- |
| Question | how dark is it **here** | **where** is it dark |
| Reads | one binary tile, ~65 KB | rendered PNG tiles, ~30 KB each |
| Shows | every intermediate, raw bytes included | colour, and a reading per click |
| Years | one at a time, six buttons | one at a time, a dropdown, **plus the trend layer** |
| Deep zoom | n/a | past zoom 8 it paints the grid itself, so it stays sharp |

The map page also carries **VIIRS night-lights layers** from
[NASA GIBS](https://worldview.earthdata.nasa.gov/), keyless and CORS-clean like everything
else here. That is the *radiance* the atlas is modelled from — where light is emitted, not
how bright the sky is above you — so it is worth a look beside the atlas and is never what
the marker reads. What GIBS publishes is the **Black Marble annual composite for 2012 and
2016** and a **nightly** NOAA-20 product from 2018 to a few nights ago (its own date box),
and it caps this projection at zoom 8. A year dropdown running to 2025, as
lightpollutionmap.info has, is that site rendering NASA's annual composites itself.

**Basemaps are Esri's** — dark canvas (the default), topo and satellite — plus
OpenStreetMap and none. OSM is not the default on purpose: its tiles are run by
volunteers for map users, and a map you pan, opened off `file://` with no Referer, gets
served *"Access blocked — app is not following the tile usage policy"* soon enough.
[`../places.js`](../places.js)'s 🗺️ 在地圖上點選 stays on OSM because it asks for one
screen once. CARTO's basemaps were tried first and are not usable keyless any more: the
tiles return `HTTP 200` but arrive stamped "API KEY REQUIRED".

**Why not [lightpollutionmap.info](https://www.lightpollutionmap.info/)**, the obvious
map to copy: its overlays are GeoServer WMS tiles on its own server, and its help
FAQ #20, headed *"We want to use your WMS/WMTS service"*, answers with "download the
GeoTIFFs, or contact me" — not with a URL. The science underneath is public (NASA Black
Marble, Falchi/Cinzano), but the rendering is his, so this page goes to the public
sources directly. There is no map library either: a slippy map is the Mercator pair, a
grid of `<img>` tiles and a drag handler, all of which
[`../places.js`](../places.js) already carries for 🗺️ 在地圖上點選.

## Why this is the only light-pollution source here

Pages hosting is static, so a demo can only call something **keyless and
CORS-enabled**. Light pollution is unusually badly served on that front:

| Source | Keyless? | CORS? |
| --- | --- | --- |
| `lightpollutionmap.info/QueryRaster` | ❌ `"Invalid or missing authentication. Please request a key for API use."` | ✅ |
| lightpollutionmap .app / .io / .net, BortleBuddy | web UIs, no documented public JSON API | — |
| **Lorenz's `binary_tiles/`** | ✅ static files | ✅ GitHub Pages sends `access-control-allow-origin: *` |

A key would be readable in page source, which is exactly why
[`cwa_opendata/`](../cwa_opendata/README.md) has no demo. Lorenz's tiles are the
only option that works, and the page credits him accordingly. It is a **courtesy
dependency on one person's static host** — nothing is vendored here — so every
failure path leaves the page saying so rather than breaking.

## What is actually in the file

**Neither SQM nor Bortle.** One logarithmically quantised integer per grid point,
and nothing else. The tile is a 5° square holding 600 × 600 points at 1/120°
(30 arcsec, ~0.9 km), delta-encoded to keep it small:

- `bytes[0..1]` — the lower-left corner, a 2-byte absolute value (`128·b0 + b1`)
- every byte after — a **signed 1-byte change** from its neighbour

To read a point you walk up column 0 to your row, then across that row, summing.
That is 360,001 bytes raw and 40–70 KB gzipped. The tiles are gzip *files* rather
than gzip-encoded responses, so the browser will not unwrap them — Lorenz's own
viewer pulls in `pako`; this page uses the built-in
[`DecompressionStream`](https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream)
instead and needs no library.

Everything after that integer is derived, and the three derivations have very
different standing:

| Row | Whose | Notes |
| --- | --- | --- |
| `ratio` | Lorenz | `(5/195)·(e^(0.0195·value) − 1)` — artificial glow ÷ natural night sky |
| `SQM` | Lorenz | `22 − 2.5·log₁₀(1 + ratio)`, mag/arcsec², bigger is darker |
| `LP Zone` | Lorenz | his own 15-step banding, `0` (darkest) to `7b` |
| **`Bortle`** | **ours** | the conventional SQM ladder — see below |

**Bortle is the one step the atlas does not endorse.** Lorenz
[declines to publish it](https://djlorenz.github.io/astronomy/lp/bortle.html):
Bortle judges the *whole* sky, light domes near the horizon included, which a
zenith number cannot see. Its cut points are not arbitrary — seven of the eight
fall exactly on LP Zone boundaries, because both ladders descend from the same
round brightness-ratio steps — but **Bortle 4 swallows zones 3a, 3b, 4a and 4b
whole** (SQM 21.69 down to 20.49), which is the entire range decent dark sites in
Taiwan occupy. Read the SQM; Bortle is there because people speak it.

## The year buttons

The atlas is published annually and old years stay put, so the same point can be
read from 2016, 2020, 2022, 2023, 2024 or 2025. That turns a snapshot into a
trend, and it is the quickest way to see a site being lost. 合歡山,
Taiwan's certified dark-sky park:

| atlas | SQM | artificial glow | LP Zone | Bortle |
| --- | --- | --- | --- | --- |
| 2016 | 21.51 | 0.57× natural | 3a | 4 |
| 2020 | 21.44 | 0.68× | 3b | 4 |
| 2022 | 21.42 | 0.71× | 3b | 4 |
| 2023 | 21.38 | 0.77× | 3b | 4 |
| 2024 | 21.39 | 0.75× | 3b | 4 |
| 2025 | 21.37 | 0.78× | 3b | 4 |

Artificial glow there has risen by about a third in nine years. Note that
**Bortle reads "4" for every one of those rows** — a second, concrete
demonstration of why the page shows the SQM above it.

## Where else this appears

The same decode runs in three places: both pages here, and
[`astro_score/astro-score_readable.html`](../astro_score/astro-score_readable.html),
where it fills the `光害 (SQM)` / `Bortle` / `LP Zone` rows. They are parallel
implementations — change one, mirror the others. The difference is only what each
shows: `astro-score_readable` needs three numbers and hides the working,
`binary-tile` is nothing but the working, and the map reads one point per click and
puts the working behind a link.

## Running

No install, no server, no key:

```bash
open light_pollution/binary-tile.html          # or any static server
open light_pollution/light_pollution_map.html
```

It works straight off `file://` because the tiles are served with
`access-control-allow-origin: *`. The one control that does not is
**📍 使用目前位置**, which fills the location box from the device's own GPS:
geolocation is a secure-context API, so it needs `https://` or `localhost`, and
says so beside the button when it is refused. **🗺️ 在地圖上點選** beside it fills
the same box from an [OpenStreetMap](https://www.openstreetmap.org/copyright) map
— drag or tap until the crosshair is on the spot, 確定 to take it — and needs
neither a permission nor a secure context, so that one does work off `file://`.
It is `pickOnMap()` in [`../places.js`](../places.js): keyless, and with no map
library behind it.

The meta line names the coordinate on a second line — 中華民國/南投縣/仁愛鄉, from
BigDataCloud's keyless `reverse-geocode-client` — as on every page with a location
box. Like the map behind 🗺️ 在地圖上點選 it is a helper for that box, not part of the
decode: fetched after the tile is on screen, never waited for, and failing to
nothing. The atlas is still the only thing this page reads a number out of.

## Credit

Data: **David J. Lorenz**, [World Atlas of Artificial Night Sky Brightness](https://djlorenz.github.io/astronomy/lp/),
a recomputation of Cinzano's original atlas. Built on NOAA/VIIRS night lights
processed by the [Earth Observation Group](https://payneinstitute.mines.edu/eog/)
at the Colorado School of Mines. It is **modelled**, not measured from the ground.
