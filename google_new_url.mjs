#!/usr/bin/env node

// Usage:
//   node google_new_url.mjs
//   node google_new_url.mjs https://news.google.com/rss/articles/CBMiV0FVX3lxTE9kMHlaaExrRzdPeEFyRXpUSlE1TXlNYnI0amRwUElmd0IwbExkTy1pX21yUVZrRE5uaUx6Q1RfX0U0dWFTQnNtNVVWOWIweFhpRS00MmQ2WQ?oc=5

const DEFAULT_URL =
  "https://news.google.com/rss/articles/" +
  "CBMijgFBVV95cUxNc3FaX1BQb0xjZHdVTFdSaTl0b1J4eVl1amVuNXE1" +
  "c29RaFowUi1hQmtyem1ENmZWb2lSQ0RyNjBIMGpvcDlDNkdOa1IwTk13" +
  "VEVFakJIeXBDVktGc2Q3S3VDV0xVakxOb3loYm5sSmZZYUtEZjFXSTBZ" +
  "QmN0b0kydV8yWVoxQ2JzZ19aM0t3?oc=5";

const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " +
  "AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/120.0.0.0 Safari/537.36";

class GoogleNewsResolveError extends Error {}

function extract(html, attr) {
  const marker = `${attr}="`;
  const i = html.indexOf(marker);
  if (i === -1) {
    throw new GoogleNewsResolveError(
      `Could not find '${attr}' in page. The link format or page structure may have changed.`
    );
  }
  const start = i + marker.length;
  const end = html.indexOf('"', start);
  return html.slice(start, end);
}

async function getRealUrl(googleNewsUrl, timeout = 15000) {
  const headers = { "User-Agent": UA };

  // Step 1: fetch article page to get signature + timestamp
  const pageRes = await fetch(googleNewsUrl, { headers, signal: AbortSignal.timeout(timeout) });
  if (!pageRes.ok) throw new GoogleNewsResolveError(`HTTP ${pageRes.status} fetching article page`);
  const html = await pageRes.text();

  const signature = extract(html, "data-n-a-sg");
  const timestamp = extract(html, "data-n-a-ts");
  const articleId = extract(html, "data-n-a-id");

  // Step 2: call batchexecute RPC
  const innerPayload = JSON.stringify([
    "garturlreq",
    [
      ["X", "X", ["X", "X"], null, null, 1, 1, "US:en", null, 1, null, null, null, null, null, 0, 1],
      "X",
      "X",
      1,
      [1, 1, 1],
      1,
      1,
      null,
      0,
      0,
      null,
      0,
    ],
    articleId,
    timestamp,
    signature,
  ]);
  const body = "f.req=" + encodeURIComponent(JSON.stringify([[["Fbv4je", innerPayload, null, "generic"]]]));

  const rpcRes = await fetch(
    "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
    {
      method: "POST",
      headers: {
        ...headers,
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body,
      signal: AbortSignal.timeout(timeout),
    }
  );
  if (!rpcRes.ok) throw new GoogleNewsResolveError(`HTTP ${rpcRes.status} from batchexecute`);

  let text = await rpcRes.text();
  if (text.startsWith(")]}'\n") || text.startsWith(")]}'")) {
    text = text.slice(text.indexOf("\n") + 1);
  }

  try {
    const outer = JSON.parse(text);
    for (const row of outer) {
      if (row[0] === "wrb.fr" && row[2]) {
        const inner = JSON.parse(row[2]);
        return inner[1];
      }
    }
  } catch (e) {
    throw new GoogleNewsResolveError(`Could not parse RPC response: ${e.message}`);
  }

  throw new GoogleNewsResolveError("Real URL not found in RPC response.");
}

const url = process.argv[2] ?? DEFAULT_URL;
console.log(url);
getRealUrl(url)
  .then((real) => console.log(real))
  .catch((e) => {
    console.error(e.message);
    process.exit(1);
  });
