# cwa_opendata

Query Taiwan CWA (Central Weather Administration) Open Data for daily sun and moon
rise/set times, and print a one-line summary.

Data source: <https://opendata.cwa.gov.tw/>

| Script | Dataset | What it does |
| --- | --- | --- |
| `cwa_sunrise.py` | `A-B0062-001` | Sunrise / sun transit / sunset time and azimuth/altitude for a county on a date, plus daylight length. |
| `cwa_moonrise.py` | `A-B0063-001` | Moonrise / moon transit / moonset for a county on a date, plus time the moon is up. |

## How it works

Both scripts hit the CWA REST datastore endpoint
`https://opendata.cwa.gov.tw/api/v1/rest/datastore/<dataset-id>` with query
parameters `Authorization` (API key), `format=JSON`, `CountyName` (e.g. `臺北市`),
`timeFrom` / `timeTo` (a date window), and `sort=Date`, then read the daily records
from `records.locations.location[0].time`.

- **Sun** is simple: fetch a 1-day window and use that day's record directly.
- **Moon** needs care: the moon rises ~50 minutes later each day, so on any given
  date one of rise/transit/set may be missing (empty string in the API response) or
  belong to an adjacent calendar day. The script fetches a 3-day window
  (yesterday/today/tomorrow) and stitches together the full rise→transit→set cycle
  that starts on the target day, prefixing times taken from adjacent days with
  `昨` (yesterday) or `明` (tomorrow).

## Running

```bash
# defaults: 臺北市, today (Asia/Taipei)
uv run cwa_sunrise.py
uv run cwa_moonrise.py

# specific county / date
uv run cwa_sunrise.py 高雄市 2026-07-15
uv run cwa_moonrise.py 高雄市 2026-07-15
```

Example output:

```
臺北市 2026-07-15
出:05:14/64.66,中:11:58/84.51,沒:18:43/295.39 (13:29)
```

## API key

The scripts read the API key from (in order):

1. the `CWA_API_KEY` environment variable, or
2. `config.yml` at the repo root (gitignored) — copy `config_example.yml` to
   `config.yml` and fill in your key:

   ```yaml
   cwa_opendata:
     api_key: CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
   ```

Free registration at <https://opendata.cwa.gov.tw/>.
