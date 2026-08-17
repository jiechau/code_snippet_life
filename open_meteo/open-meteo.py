# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
#
# uv run open-meteo.py
# or
# uv run open-meteo.py 24.1375,121.2745
# or
# uv run open-meteo.py 24.1375,121.2745 forecast_hours=24
# or
# uv run open-meteo.py models= hourly=cloud_cover
#
# Minimal demonstration of a single Open-Meteo forecast API call. Prints the
# exact JSON the API returned with one key added -- get_para, the full request
# URL -- so the same call can be replayed in a browser or with curl.
#
# Request metadata (status, content type, size, elapsed) goes to stderr, so
# stdout stays clean JSON:
#
#   uv run open-meteo.py > forecast.json
#   uv run open-meteo.py | jq '.hourly | keys'

import json
import sys
from urllib.parse import urlencode

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Taipei, matching the other snippets in this folder.
DEFAULT_LAT, DEFAULT_LON = 25.033, 121.565
DEFAULT_DAYS = 7

HOURLY_VARS = [
    "cloud_cover",
    "cloud_cover_low",
    "cloud_cover_mid",
    "cloud_cover_high",
    "visibility",
    "precipitation_probability",
    "relative_humidity_2m",
    "dew_point_2m",
    "wind_speed_10m",
    "temperature_2m",
]

MODELS = ["ecmwf_ifs025", "gfs_global", "jma_gsm", "icon_global"]


def default_params(lat: float, lon: float, days: int = DEFAULT_DAYS) -> dict:
    """The request milkyway.py makes, as a plain dict."""
    return {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "models": ",".join(MODELS),
        "timezone": "auto",
        "forecast_days": days,
    }


def build_url(params: dict) -> str:
    """
    The full GET URL for a parameter dict.

    Commas are left literal (`safe=","`) so the hourly/models lists stay
    readable and match Open-Meteo's own documented examples; requests would
    otherwise percent-encode them to %2C. This exact string is what gets
    requested, so the get_para returned to the caller is the real URL rather
    than a prettified reconstruction of it.
    """
    return f"{FORECAST_URL}?{urlencode(params, safe=',')}"


def fetch(params: dict, timeout: int = 30) -> tuple[dict, requests.Response]:
    """
    Call the API and return (body, response).

    The body is exactly what Open-Meteo sent, decoded, plus the single added
    key get_para. Errors are returned rather than raised: Open-Meteo answers a
    bad request with HTTP 400 and a JSON body like
    {"error": true, "reason": "Latitude must be in range of -90 to 90°..."},
    which is far more useful to see than a stack trace.
    """
    url = build_url(params)
    resp = requests.get(url, timeout=timeout)
    try:
        body = resp.json()
    except ValueError:
        # Not JSON at all -- hand back the raw text so the caller can see it.
        body = {"error": True, "reason": "response was not JSON", "text": resp.text}
    body["get_para"] = url
    return body, resp


def parse_args(argv: list[str]) -> dict:
    """
    Build the request parameters from the command line.

    With no arguments the defaults above are used. A bare "lat,lon" argument
    sets the location; any "key=value" argument overrides or adds a query
    parameter, and an empty value ("models=") drops one entirely -- handy for
    seeing how the response shape changes when the model list goes away.
    """
    lat, lon, overrides = DEFAULT_LAT, DEFAULT_LON, {}

    for arg in argv:
        if "=" in arg:
            key, _, value = arg.partition("=")
            overrides[key] = value
        elif "," in arg:
            lat_s, _, lon_s = arg.partition(",")
            try:
                lat, lon = float(lat_s), float(lon_s)
            except ValueError:
                raise SystemExit(f'Bad location "{arg}": expected "lat,lon"')
        else:
            raise SystemExit(
                f'Bad argument "{arg}": expected "lat,lon" or "key=value"'
            )

    params = default_params(lat, lon)
    for key, value in overrides.items():
        if value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return params


if __name__ == "__main__":
    params = parse_args(sys.argv[1:])
    body, resp = fetch(params)

    print(
        f"HTTP {resp.status_code}  {resp.headers.get('Content-Type')}  "
        f"{len(resp.content)} bytes  {resp.elapsed.total_seconds():.2f}s",
        file=sys.stderr,
    )
    print(json.dumps(body, indent=2, ensure_ascii=False))

    if not resp.ok:
        sys.exit(1)
