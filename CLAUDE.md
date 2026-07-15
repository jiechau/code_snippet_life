# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of small, **self-contained** code snippets. Each snippet lives in its own
top-level folder (e.g. `google_news_url/`) and is independent — there is no shared
library, build system, package manifest, or test suite at the repo root. The root
`README.md` is an index table; every snippet folder has its own `README.md` describing
what it does and how to run it.

## Conventions when adding or editing snippets

- **One folder per snippet.** Keep everything a snippet needs inside its folder. Do not
  introduce cross-snippet imports or a shared root package.
- **Each snippet folder gets its own `README.md`**, and the new snippet must be added as a
  row to the table in the root `README.md`.
- **Parallel implementations stay equivalent.** Some snippets ship the same logic in
  multiple runtimes (e.g. `google_new_url.py` and `google_new_url.mjs`). When you change
  the behavior of one, mirror it in the other so they produce identical output.
- **Python snippets use `uv` with inline PEP 723 dependencies** declared in a
  `# /// script` header — no `requirements.txt` or virtualenv setup. They run with
  `uv run <file>.py`, which installs declared deps automatically.
- **Node snippets target Node 18+** and prefer built-ins (`fetch`, `AbortSignal.timeout`)
  with no external packages / no `package.json`.
- Scripts take their input as `argv[1]` and fall back to a hard-coded default URL/value so
  they can be run with no arguments for a quick smoke test.

## Running

```bash
# Python (deps auto-installed from the PEP 723 header)
uv run google_news_url/google_new_url.py [arg]

# Node (no install step)
node google_news_url/google_new_url.mjs [arg]
```

There is no lint or test command; verify a snippet by running it.

## cwa_opendata specifics

Queries Taiwan CWA Open Data REST datastore endpoints
(`https://opendata.cwa.gov.tw/api/v1/rest/datastore/<dataset-id>`) with an API key
(`Authorization` query param), `CountyName`, and a `timeFrom`/`timeTo` date window.
The key comes from the `CWA_API_KEY` env var or root `config.yml` (gitignored; see
`config_example.yml`) — never hard-code credentials in snippets. `cwa_sunrise.py` uses dataset `A-B0062-001` (a 1-day
window); `cwa_moonrise.py` uses `A-B0063-001` with a 3-day window (yesterday/today/
tomorrow) because moon rise/transit/set can be missing on a given date or fall on an
adjacent day — `pick_moon_events()` stitches the cycle together, labeling borrowed
times with 昨/明. Note: the site's TLS certificate lacks a Subject Key Identifier, so
both scripts relax `ssl.VERIFY_X509_STRICT` (Python 3.13 default) via a custom
`HTTPAdapter` while keeping normal certificate verification.

## google_news_url specifics

Resolves a Google News redirect link (from the search RSS feed) to the real article URL by
mimicking the browser: (1) `GET` the article page to scrape the `data-n-a-sg` (signature),
`data-n-a-ts` (timestamp), and `data-n-a-id` attributes, then (2) `POST` those to the
`batchexecute` RPC (`rpcids=Fbv4je`) and parse the real URL out of the `wrb.fr` row. This
depends on Google's page structure and RPC payload shape — if Google changes either, the
attribute scraping or response parsing is what breaks.
