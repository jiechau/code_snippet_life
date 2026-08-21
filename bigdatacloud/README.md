# bigdatacloud

Reverse geocoding with [BigDataCloud](https://www.bigdatacloud.com/) — coordinates
in, place names out. **No API key required** for the `-client` endpoints: they are
designed to be called straight from a browser, and the free tier allows 50,000
requests/month with no signup.

**API reference:
<https://www.bigdatacloud.com/docs/api/reverse-geocode-to-city-api>** — the full
field list, the `localityInfo` structure, and the other (key-requiring) variants of
the same lookup.

**Live demo:** https://jiechau.github.io/code_snippet_life/bigdatacloud/

- [reverse-geocode API](https://jiechau.github.io/code_snippet_life/bigdatacloud/reverse-geocode.html)
  — one call, raw JSON plus the request URL.

This folder holds **no script**, only the demo page: the call is a single keyless
`GET` with two meaningful parameters, so there is nothing a Python version would
demonstrate that the page does not. The page is therefore named after the endpoint
it calls rather than after a script it ports.

## The endpoint

```
GET https://api.bigdatacloud.net/data/reverse-geocode-client
      ?latitude=24.5145449&longitude=121.8277122&localityLanguage=zh
```

The response is a flat set of place names plus a nested `localityInfo`:

```json
{
  "latitude": 24.5145449,
  "longitude": 121.8277122,
  "lookupSource": "coordinates",
  "localityLanguageRequested": "zh",
  "continent": "亚洲",
  "continentCode": "AS",
  "countryName": "中華民國",
  "countryCode": "TW",
  "principalSubdivision": "宜蘭縣",
  "principalSubdivisionCode": "TW-ILA",
  "city": "南澳鄉",
  "locality": "蘇澳鎮",
  "postcode": "",
  "plusCode": "7QP3GR7H+R3",
  "localityInfo": { "administrative": [ ... ], "informative": [ ... ] }
}
```

Notes on the fields, all of which the demo page's own JSON pane will show you:

- **`localityLanguage` is a request for translated names, not for a different
  place.** With `zh` the country comes back as 中華民國 and the county as 宜蘭縣;
  with `en` the same coordinates give Taiwan / Yilan County. It takes an ISO 639-1
  code and falls back to English where no translation exists.
- **`city` and `locality` are the two least reliable fields.** They come from
  different administrative layers and can disagree with local expectation — the
  east-coast example above puts 南澳鄉 in `city` and neighbouring 蘇澳鎮 in
  `locality`. Over open water or in sparse terrain either can be an empty string.
- **`localityInfo.administrative` is the raw layer stack** the flat fields are
  distilled from: an entry per admin level with OSM/Wikidata/GeoNames ids. It is
  most of the response by size, and it is where a name that looks wrong in the flat
  fields can be traced. Note its `adminLevel: 2` entry for Taiwan carries the PRC's
  naming (中国台湾, `CN-TW`) alongside `countryName: 中華民國` — the API reports
  what its upstream sources say, and they do not agree with each other.
- **`postcode` is empty for Taiwan** — BigDataCloud has postal data for a list of
  countries and this is not one of them. Same for any coordinate at sea.
- **`city` frequently repeats `principalSubdivision`** in a directly administered
  municipality: 三總 (25.070602, 121.592399) gives 臺北市 for both, with 內湖區 in
  `locality`. That is why the join below drops duplicates.

## `reverse-geocode.html`

Listed as **reverse-geocode API** on the folder's index page. Deliberately the same
page as [`open_meteo/open-meteo.html`](../open_meteo/README.md) — same layout, same
behaviour, same request core — with the form cut down to the one input this endpoint
needs:

- **location** — a `lat,lon` box with **📍 使用目前位置** beside it and the saved
  spots wrapped onto a line of their own: 輸入, 瑞光路, 大崙頭山, 大武崙砲台, 內洞停車場, 烏石港, 東澳, 石梯坪, 柚子湖,
  龍磐公園, 暗空公園.
  Clicking one fills the coordinates and refetches; the pressed button shows which
  spot is displayed, and a hand-typed coordinate presses none. They come from the
  `PLACES` array in [`../places.js`](../places.js), shared by every demo page in the
  repo, whose first entry is also the default location.
- **使用目前位置 (use current position)** — the device's own GPS into the box, and
  into 輸入, `PLACES[0]`, the one entry that is not a saved spot. Geolocation is a
  secure-context API, so it needs the published `https://` page or `localhost`, not
  `file://`; a refusal is printed beside the button rather than thrown, and nothing
  is stored.

`localityLanguage` is fixed at `zh` in the page rather than exposed as a field, so
location really is the only input. Change the constant to see other languages.

Submitting shows the request URL as a clickable link and the pretty-printed JSON,
under a one-line request summary in the same format the other demos use:

```
HTTP 200  application/json; charset=utf-8  2775 bytes  0.31s
中華民國/宜蘭縣/南澳鄉/蘇澳鎮
```

That second line is `countryName/principalSubdivision/city/locality` joined, with
blanks and duplicates dropped — the exact string
[`astro_score/astro-score_readable.html`](../astro_score/README.md) puts on its own
meta line, which is the only place this endpoint is consumed in the repo. It is
shown here because it is the payoff of the call: four fields out of a ~2.8 KB
response, and both the fields and the join are visible on the same screen. The join
is a copy of that page's `reverseGeocode()`, so **changing one means changing the
other**. Nothing else on the page is computed — the JSON is exactly what came back,
with no key added.

Like the Open-Meteo demos, an API error is *displayed* rather than thrown: a bad
latitude answers with a JSON body naming the problem, which is more useful than a
stack trace. Do not read too much into the numbers in it — `latitude=999` comes back
as HTTP **400** carrying `{"status": 401, "description": "invalid coordinates..."}`,
so the body's `status` is not the HTTP status. The meta line reports the real one.

It talks to BigDataCloud **straight from the browser**, which works for the same two
reasons Open-Meteo does: no API key (a key would be readable in page source) and
`access-control-allow-origin: *` on the `-client` endpoints. The key-requiring
variants of this lookup are *not* CORS-open and could not be demoed here.

`index.html` is just the list page for this folder — one link per demo, reached from
the root hub.

Open it locally with any static server (`python3 -m http.server`, then
<http://localhost:8000/bigdatacloud/>) or just open the file directly — it has no
build step and no dependencies.
