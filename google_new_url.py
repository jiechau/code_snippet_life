# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
#
# uv run google_new_url.py
# or
# uv run google_new_url.py https://news.google.com/rss/articles/CBMiV0FVX3lxTE9kMHlaaExrRzdPeEFyRXpUSlE1TXlNYnI0amRwUElmd0IwbExkTy1pX21yUVZrRE5uaUx6Q1RfX0U0dWFTQnNtNVVWOWIweFhpRS00MmQ2WQ?oc=5

import json
import requests


class GoogleNewsResolveError(Exception):
    pass


def get_real_url(google_news_url: str, timeout: int = 15) -> str:
    """
    Resolve a Google News article/read-more URL to its real destination URL.

    Mimics what the browser does:
      1. GET the Google News article page to extract the per-article
         signature + timestamp that Google embeds for the RPC.
      2. POST to the batchexecute RPC with the token + signature + timestamp.
      3. Parse the real URL out of the RPC response.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    })

    # --- Step 1: fetch the article page to get signature + timestamp ---
    page = session.get(google_news_url, timeout=timeout)
    page.raise_for_status()
    html = page.text

    def _extract(attr: str) -> str:
        marker = f'{attr}="'
        i = html.find(marker)
        if i == -1:
            raise GoogleNewsResolveError(
                f"Could not find '{attr}' in page. "
                "The link format or page structure may have changed."
            )
        i += len(marker)
        j = html.find('"', i)
        return html[i:j]

    signature = _extract("data-n-a-sg")
    timestamp = _extract("data-n-a-ts")
    article_id = _extract("data-n-a-id")

    # --- Step 2: call the batchexecute RPC ---
    payload = [
        "Fbv4je",
        json.dumps([
            "garturlreq",
            [["X", "X", ["X", "X"], None, None, 1, 1,
              "US:en", None, 1, None, None, None, None, None, 0, 1],
             "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
            article_id, timestamp, signature,
        ]),
    ]
    body = "f.req=" + requests.utils.quote(json.dumps([[payload]]))

    rpc = session.post(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute",
        params={"rpcids": "Fbv4je"},
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        timeout=timeout,
    )
    rpc.raise_for_status()

    text = rpc.text
    if text.startswith(")]}'"):
        text = text[text.find("\n") + 1:]

    try:
        outer = json.loads(text)
        for row in outer:
            if row[0] == "wrb.fr" and row[2]:
                inner = json.loads(row[2])
                return inner[1]
    except (ValueError, IndexError, TypeError) as e:
        raise GoogleNewsResolveError(f"Could not parse RPC response: {e}")

    raise GoogleNewsResolveError("Real URL not found in RPC response.")


if __name__ == "__main__":
    import sys
    default_url = (
        "https://news.google.com/rss/articles/"
        "CBMijgFBVV95cUxNc3FaX1BQb0xjZHdVTFdSaTl0b1J4eVl1amVuNXE1"
        "c29RaFowUi1hQmtyem1ENmZWb2lSQ0RyNjBIMGpvcDlDNkdOa1IwTk13"
        "VEVFakJIeXBDVktGc2Q3S3VDV0xVakxOb3loYm5sSmZZYUtEZjFXSTBZ"
        "QmN0b0kydV8yWVoxQ2JzZ19aM0t3?oc=5"
    )
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    print(url)
    print(get_real_url(url))
