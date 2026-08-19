# pure_math

The astronomy behind [`astro_score/`](../astro_score/README.md), one formula per
page. **No script, and no API call at all** — every page is numbers in, numbers
out, so there is nothing to install and nothing to go down.

These are extractions, not new work: each page lifts one block out of
[`astro_score/astro-score_readable.html`](../astro_score/astro-score_readable.html)
and shows it on its own, with every intermediate value printed instead of folded
into a grid cell. When that page draws 太陽 −6.6° for an hour, this is where you
can see the eight lines of arithmetic that produced the number.

**Live demo:** https://jiechau.github.io/code_snippet_life/pure_math/

| Page | Answers | Lifted from |
| --- | --- | --- |
| [galactic_center.html](galactic_center.html) | How high is the Milky Way core? | the `銀心` and `銀心 (max)` rows |
| [sun_phase.html](sun_phase.html) | Is it dark yet? | the `太陽` row, and the gate that zeroes 觀星 |
| [moon_phase.html](moon_phase.html) | Is the moon up, and how bright? | the `月亮` and `月相` rows, plus 月亮扣分 |

Each takes a time and a `lat,lon` (the saved spots from
[`places.js`](../places.js) are offered as buttons) and prints three things: the
answer as a few cards, then a table of every intermediate — Julian Day, sidereal
time, the series terms, the spherical-triangle conversion — with the formula that
produced each one. Committing either input recomputes; there is no request in
flight to wait for, so the button is a formality.

## The time is local to the place you picked

The time box holds **local wall time at the location**, not UTC, and the offset is
**computed from the longitude** rather than looked up: the sun crosses 15° an hour,
so `zoneOffsetHours(lon)` is `round(lon / 15)`. All ten saved spots land on
**UTC+8**, which is Taiwan's real offset. The label beside the field says which
offset was assumed, and the meta line prints both readings of the instant
(`12:36 UTC+8 (= 04:36 UTC)`) so nothing is hidden.

Being able to type "22:00 tonight at 龍磐公園" is the point — that is the question
these pages get asked. Changing the location keeps the reading and moves the
instant, which is the intuitive behaviour: 22:00 means 22:00 wherever you are
going.

**It is the solar zone, not the legal one.** Real time zones are drawn by
legislatures, so geometry and law part company wherever a country runs one clock
across a wide span (western China), keeps a neighbour's (Spain), or sits far from
its meridian — Iceland at −22° gets `UTC−1` here but actually runs `UTC+0`. There
is **no DST** either. The consequence is contained and worth being clear about:
the offset only *labels the input*, since everything downstream is computed from
the UTC instant it produces. So where the legal zone differs, the wall-clock
reading is an hour or two out while **every angle stays exact**. Fixing that
properly would mean shipping a table of zone boundaries — a dataset, when the point
of this folder is that it computes rather than looks up.

The browser's own zone is never consulted, so a coordinate and a reading mean the
same thing on any machine. `astro-score_readable.html` solves the same problem the
other way round, because Open-Meteo hands it local wall time plus a
`utc_offset_seconds` to convert with.

## Why no API and no script

Open-Meteo returns sunrise, sunset and `daily=moon_phase` — nothing hourly, and
nothing at all about the galactic core. So `astro_score` computes these angles
locally from Meeus' low-precision series, and that arithmetic is the only part of
it that needs no network. Pulling it onto its own pages is therefore free: a
Python version would demonstrate nothing the browser cannot, which is the same
reason [`bigdatacloud/`](../bigdatacloud/README.md) has no script either.

Accuracy is what the series give and no more: the sun to about 0.01°, the moon to
about 0.3° in longitude. Neither has a refraction correction, and the moon's
altitude is geocentric — no parallax — so near the horizon it can be off by up to
about a degree. That is far inside the tolerance of "is it dark" and "is the moon
up", which is all the score asks. Do not read these pages as an ephemeris.

## What is copied from where

Per the one-folder-per-snippet rule, nothing is imported: each page carries its
own copy of the functions it needs, and **only** the ones it draws.
`galactic_center.html` has no ecliptic conversion at all (Sagittarius A* is a
fixed equatorial position), and only `moon_phase.html` carries the lunar series —
along with `sunPosition()`, because the illuminated fraction is a function of the
moon–sun elongation and so cannot be had without the sun.

Every shared function is **byte-identical** to
`astro_score/astro-score_readable.html`'s, which is in turn verified against
`astro_score/milkyway.py` to four decimal places. The two deliberate exceptions:

- **`moonPosition()` returns five extra fields** (`lp`, `d`, `m`, `mp`, `f`, and
  `eclLat`). Every computed term is unchanged — the return object is wider
  because this page draws the five fundamental arguments as rows of their own.
- **`moonPhaseName()` / `MOON_PHASE_NAMES` are new to JavaScript.**
  `astro-score_readable.html` shows 月相 as a percentage only, so the Chinese
  names (新月 / 眉月 / 上弦 / 盈凸 / 滿月, and their waning counterparts) are ported
  straight from `milkyway.py`'s `moon_phase_name()`. Those two are now the pair
  to keep in step.

Verified across 24 (instant, place) combinations — Taiwan, Atacama, Reykjavík,
1970 to 2099 — against `milkyway.py`: every angle agrees to within 1e-13°, and
every phase name matches exactly.

The page chrome (the `<style>` block, the location row, `show()`, the submit
handler) is a copy of
[`bigdatacloud/reverse-geocode.html`](../bigdatacloud/reverse-geocode.html)'s,
with `Fetch` renamed `Compute` and the URL and JSON panes replaced by the cards
and the step table. Its policy of *displaying* a bad input rather than throwing is
kept.

## Running

No build, no server needed — open a page straight off disk:

```bash
open pure_math/galactic_center.html
```

`../places.js` is a classic script, so `file://` works. Or serve the repo root
with `python3 -m http.server` and browse to `/pure_math/`.
