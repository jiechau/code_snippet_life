# code_snippet_life

A collection of small, self-contained code snippets. Each snippet lives in its own folder with its own `README.md` describing what it does and how to run it.

## Snippets

| Snippet | Description |
| --- | --- |
| [google_news_url/](google_news_url/README.md) | Resolve a Google News redirect URL (e.g. from an RSS feed) to its real destination URL. Python and Node implementations. |
| [cwa_opendata/](cwa_opendata/README.md) | Query Taiwan CWA Open Data for daily sunrise/sunset (`cwa_sunrise.py`) and moonrise/moonset (`cwa_moonrise.py`) times per county. |
| [open_meteo/](open_meteo/README.md) | Open-Meteo weather API (no key needed): a raw one-call demo returning the exact JSON plus the request URL (`open-meteo.py`), and a scorer for how suitable each upcoming hour is for Milky Way astrophotography at a GPS location (`milkyway.py`). |

## Demo pages

Some snippets have a browser demo. Pushing to `main` publishes the repo as a
static site — GitLab Pages via [`.gitlab-ci.yml`](.gitlab-ci.yml), GitHub Pages
via [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

Pages are two levels of list: the root [`index.html`](index.html) links to one
`<snippet>/index.html` per snippet folder, and that folder list links to one page
per demo, each named after the script it ports.

| Page | Demo of |
| --- | --- |
| [open_meteo/open-meteo.html](open_meteo/open-meteo.html) | `open_meteo/open-meteo.py` — fill in the arguments, submit, see the request URL and the returned JSON. |
| [open_meteo/open-meteo_readable.html](open_meteo/open-meteo_readable.html) | The same request, drawn as an hour-by-hour forecast grid: a tab per model, a row per variable, plus locally computed sun/moon angles — colour-coded and scrollable. |

Pages hosting is **static**, so a demo page cannot run the Python; it re-implements
the snippet in JavaScript and calls the upstream API directly from the browser.
That is only possible for keyless, CORS-enabled APIs like Open-Meteo — a snippet
needing a credential (`cwa_opendata`) or a cross-origin scrape (`google_news_url`)
cannot be demoed this way without a server, which is why those rows are absent.
Where a page and a script are two implementations of the same snippet, changing
one means mirroring the other.

Preview locally with any static server:

```bash
python3 -m http.server   # then open http://localhost:8000/
```
