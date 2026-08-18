# code_snippet_life

A collection of small, self-contained code snippets. Each snippet lives in its own folder with its own `README.md` describing what it does and how to run it.

**Live demo:** https://jiechau.github.io/code_snippet_life/index.html

## Snippets

| Snippet | Description |
| --- | --- |
| [google_news_url/](google_news_url/README.md) | Resolve a Google News redirect URL (e.g. from an RSS feed) to its real destination URL. Python and Node implementations. |
| [cwa_opendata/](cwa_opendata/README.md) | Query Taiwan CWA Open Data for daily sunrise/sunset (`cwa_sunrise.py`) and moonrise/moonset (`cwa_moonrise.py`) times per county. |
| [open_meteo/](open_meteo/README.md) | Open-Meteo weather API (no key needed): a raw one-call demo returning the exact JSON plus the request URL (`open-meteo.py`), and a scorer for how suitable each upcoming hour is for Milky Way astrophotography at a GPS location (`milkyway.py`). |

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

Pages are two levels of list: the root [`index.html`](index.html) links to one
`<snippet>/index.html` per snippet folder, and that folder list links to one page
per demo, each named after the script it ports.

| Page | Demo of |
| --- | --- |
| [open_meteo/open-meteo.html](open_meteo/open-meteo.html) | `open_meteo/open-meteo.py` — fill in the arguments, submit, see the request URL and the returned JSON. All three Open-Meteo pages also name the place the coordinates fall in (中華民國/宜蘭縣/南澳鄉/蘇澳鎮) via a second keyless API, BigDataCloud's reverse geocoder. |
| [open_meteo/open-meteo_readable.html](open_meteo/open-meteo_readable.html) | The same request, drawn as an hour-by-hour forecast grid: a tab per model, a row per variable, plus locally computed sun/moon angles — colour-coded and scrollable. |
| [open_meteo/milkyway_readable.html](open_meteo/milkyway_readable.html) | The same grid cut down to what stargazing needs: one model, the cloud decks only, and a 銀河 score per hour — `(100 − 雲量) × (100 − 月亮扣分) / 100`, zeroed while the sun is above −10°, where 月亮扣分 ramps 0 → 100 as the moon climbs 0° → 10°. Loosely after `open_meteo/milkyway.py`. |
| [google_news_url/google_new_url.html](google_news_url/google_new_url.html) | `google_news_url/google_new_url.py` — search the Google News RSS feed for a keyword, sort by `<pubDate>`, and resolve the newest N redirect links to real article URLs. **Requires a CORS proxy** (picked in the page). |

Pages hosting is **static**, so a demo page cannot run the Python; it re-implements
the snippet in JavaScript and calls the upstream API directly from the browser.
That is straightforward for a keyless, CORS-enabled API like Open-Meteo. A snippet
needing a credential (`cwa_opendata`) has no demo, because the key would be readable
in page source. `google_news_url` scrapes `news.google.com`, which sends no
`Access-Control-Allow-Origin` at all, so its page routes every request through a
user-selected public CORS proxy — that works, but those proxies are flaky and
rate-limited, so expect some rows to fail. Where a page and a script are two
implementations of the same snippet, changing one means mirroring the other.

Preview locally with any static server:

```bash
python3 -m http.server   # then open http://localhost:8000/
```
