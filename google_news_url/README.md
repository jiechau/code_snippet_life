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

### It needs a CORS proxy — your own

`news.google.com` sends no `Access-Control-Allow-Origin`, so the browser cannot call it
directly. Every request — the feed, each article page, the RPC POST — goes through the
proxy you type into the form:

- **CORS proxy** — a URL template. `{url}` is replaced with the percent-encoded upstream
  URL, `{raw}` with it verbatim; with neither, the encoded URL is appended to whatever you
  typed. So `https://your-proxy.example.com/proxy?url={url}` and
  `https://your-worker.workers.dev/?{raw}` are both fine.
- **帳號 / 密碼** — HTTP basic auth for that proxy, sent as an `Authorization` header.
  Leave both blank for an open proxy.
- **記住 proxy 設定** — off by default. Ticked, all three fields (the password included) are
  kept in this browser's `localStorage` under `google_news_url_proxy`, so the next visit has
  them filled in; unticking deletes the entry immediately, and editing a field while it is
  ticked keeps the stored copy in step, so a reload restores what was last *used* rather
  than what was first typed. Storage is per-origin, so nothing leaves the browser and the
  published GitHub and GitLab copies remember separately. Every access is wrapped in
  `try`/`catch` — Safari throws outright on `file://`, and a browser set to block site data
  throws on read as well as write — so it degrades to "the boxes start empty" and says so
  beside the checkbox.

The three fields together are one unit: a proxy URL without its credentials is no more use
than the credentials without the URL, so they are stored under a single entry rather than
one each. This is the same opt-in idiom as `cwa_opendata`'s 記住金鑰, for the same reason —
a credential should not be squirrelled away because a page was visited, but retyping a URL
and a password on every reload is the friction that makes a demo not get used.

The page shipped with a dropdown of free public proxies and no longer does — every one of
them was dead, rate-limited, or dropped POST bodies. Run your own.

**The proxy must forward POST, not just GET.** Step 1 is a GET per article page, but step 2
is a `POST` to `batchexecute`, and Google answers `405` to a GET there — there is no
GET-only route through this. A GET-only proxy gets through step 1 and then fails every row
with `HTTP 405 — proxy 不接受 POST`. What it needs to do:

- accept `POST` alongside `GET`, forwarding the request body **verbatim as raw bytes**
  (it arrives as `f.req=%5B%5B%5B…`, up to ~64 KB for a 20-article chunk) and the client's
  `Content-Type` unchanged;
- pass the upstream status, body and content-type straight back (the RPC body starts with
  `)]}'` — leave it alone);
- send `Access-Control-Allow-Methods: GET, POST, OPTIONS` and
  `Access-Control-Allow-Headers: Authorization, Content-Type`, and answer the `OPTIONS`
  preflight **without** requiring auth, since browsers preflight anonymously. Sending
  basic auth makes every request preflighted, so if `POST` is missing from that header the
  request never leaves the browser and `fetch()` rejects with a bare `TypeError` rather
  than a status.

Also expect: resolving one link means downloading its Google News article page (~570 KB) to
scrape `data-n-a-sg`, so 20 links pull ~12 MB through the proxy. The page fetches these with
a worker pool (default 6) and has a 中止 button. Failures are reported per row rather than
aborting the run.

The article URLs are requested with `&hl=en-US&gl=US&ceid=US:en` pinned; without it Google
answers `302` to that same URL and not every proxy follows redirects.
