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
