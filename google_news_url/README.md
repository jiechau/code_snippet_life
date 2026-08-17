# google_news_url

Google News links (e.g. from RSS feeds) don't point directly to the article — they go through Google's redirect system. These scripts resolve a Google News redirect URL to its real destination URL.

## Where these URLs come from

Google News exposes a search RSS feed. For example, searching for `優惠` in the Taiwan / Traditional Chinese edition:

```
https://news.google.com/rss/search?hl=zh-TW&gl=TW&ceid=TW:zh-Hant&q=%E5%84%AA%E6%83%A0
```

Query parameters:

- `q` — the search term, URL-encoded (`%E5%84%AA%E6%83%A0` = `優惠`)
- `hl` — UI language (`zh-TW`)
- `gl` — geographic edition (`TW`)
- `ceid` — country:language of the edition (`TW:zh-Hant`)

The feed is RSS/XML. Each article is an `<item>`, and the `<link>` under every `<item>` is exactly the kind of Google News redirect URL these scripts resolve:

```xml
<item>
  <title>…</title>
  <link>https://news.google.com/rss/articles/CBMi…?oc=5</link>
  <pubDate>…</pubDate>
  …
</item>
```

So the workflow is: fetch the search feed → collect every `<link>` under each `<item>` → run each one through these scripts to get the real article URL.

## How it works

Mimics what the browser does:

1. `GET` the Google News article page to extract the per-article signature + timestamp (`data-n-a-sg`, `data-n-a-ts`, `data-n-a-id`) that Google embeds for the RPC.
2. `POST` to the `batchexecute` RPC with the article id + signature + timestamp.
3. Parse the real URL out of the RPC response.

Two equivalent implementations are provided — pick whichever runtime you have.

## Python usage

```bash
# resolve the built-in default URL
uv run google_new_url.py

# resolve a specific Google News URL
uv run google_new_url.py "https://news.google.com/rss/articles/CBMiV0FVX3lxTE9kMHlaaExrRzdPeEFyRXpUSlE1TXlNYnI0amRwUElmd0IwbExkTy1pX21yUVZrRE5uaUx6Q1RfX0U0dWFTQnNtNVVWOWIweFhpRS00MmQ2WQ?oc=5"
```

Dependencies (`requests`) are declared inline via [PEP 723](https://peps.python.org/pep-0723/) script metadata, so `uv run` installs them automatically.

## Node usage

```bash
# resolve the built-in default URL
node google_new_url.mjs

# resolve a specific Google News URL
node google_new_url.mjs "https://news.google.com/rss/articles/CBMiV0FVX3lxTE9kMHlaaExrRzdPeEFyRXpUSlE1TXlNYnI0amRwUElmd0IwbExkTy1pX21yUVZrRE5uaUx6Q1RfX0U0dWFTQnNtNVVWOWIweFhpRS00MmQ2WQ?oc=5"
```

Requires Node 18+ (uses the built-in `fetch` and `AbortSignal.timeout`). No external packages.

## Output

Both print the input URL on the first line and the resolved real URL on the second.

## Browser demo

[`google_new_url.html`](google_new_url.html) does the whole workflow described above in the
browser: type a keyword (default `優惠`) and a count (default 20), and it fetches the search
feed, sorts the items by `<pubDate>` newest first, keeps the first N, and resolves every
`<link>`. Only the URL is converted — no article text is displayed.

It differs from the two scripts in one way that matters. `batchexecute` is a *batch* RPC, so
instead of one POST per link the page collects every signature first and resolves them in a
single POST (chunked at 20). The response rows come back **out of order**, tagged with the
request id in `row[6]`, so results are matched by id — matching by position silently returns
the wrong article for the wrong row.

### It needs a CORS proxy

`news.google.com` sends no `Access-Control-Allow-Origin`, so the browser cannot call it
directly. Every request — the feed, each article page, the RPC POST — goes through the
proxy chosen in the page's dropdown, which also offers a custom field (`{url}` for the
percent-encoded upstream URL, `{raw}` for it verbatim) if you run your own.

Two things to expect:

- Resolving one link still means downloading its Google News article page (~570 KB) to
  scrape `data-n-a-sg`, so 20 links pull ~12 MB through the proxy. The page fetches these
  with a worker pool (default 6) and has a 中止 button.
- Free public proxies go down and rate-limit aggressively. If rows fail, switch proxy or
  lower the count. A proxy that does not forward POST bodies will get through step 1 and
  then fail the whole resolve step.

The article URLs are requested with `&hl=en-US&gl=US&ceid=US:en` pinned; without it Google
answers `302` to that same URL and not every proxy follows redirects.
