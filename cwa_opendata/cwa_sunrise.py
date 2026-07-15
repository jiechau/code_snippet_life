# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "pyyaml",
# ]
# ///
#
# uv run cwa_sunrise.py
# or
# uv run cwa_sunrise.py 高雄市
# or
# uv run cwa_sunrise.py 高雄市 2026-07-15

import os
import ssl
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml
from requests.adapters import HTTPAdapter

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yml"


def _load_api_key() -> str:
    """
    CWA Open Data platform API key (https://opendata.cwa.gov.tw/), from the
    CWA_API_KEY environment variable or config.yml at the repo root
    (see config_example.yml).
    """
    key = os.environ.get("CWA_API_KEY")
    if key:
        return key
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)["cwa_opendata"]["api_key"]
    raise SystemExit(
        f"No API key found: set CWA_API_KEY or copy config_example.yml to "
        f"{CONFIG_PATH} and fill in your key."
    )


CWA_API_KEY = _load_api_key()

# A-B0062-001: daily sunrise / sun transit / sunset times per county
DATASET_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001"


class _CWAAdapter(HTTPAdapter):
    # opendata.cwa.gov.tw's certificate chain lacks a Subject Key Identifier,
    # which Python 3.13's default VERIFY_X509_STRICT rejects. Relax only that
    # flag; normal certificate verification stays on.
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _session() -> requests.Session:
    s = requests.Session()
    s.mount("https://", _CWAAdapter())
    return s


def get_sun_times(county: str, day: date, timeout: int = 15) -> dict:
    """
    Fetch sunrise/transit/sunset data for a Taiwan county on a given date.

    Returns the raw record for that day, e.g.:
      {"Date": "2026-07-15",
       "SunRiseTime": "05:14", "SunRiseAZ": "64.66",
       "SunTransitTime": "11:58", "SunTransitAlt": "84.51",
       "SunSetTime": "18:43", "SunSetAZ": "295.39", ...}
    """
    params = {
        "Authorization": CWA_API_KEY,
        "format": "JSON",
        "CountyName": county,
        "timeFrom": day.isoformat(),
        "timeTo": (day + timedelta(days=1)).isoformat(),
        "sort": "Date",
    }
    resp = _session().get(DATASET_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    times = data["records"]["locations"]["location"][0]["time"]
    return times[0]


def _daylight(rise: str, set_: str) -> str:
    """Daylight length between two HH:MM times, as H:MM."""
    rise_h, rise_m = map(int, rise.split(":"))
    set_h, set_m = map(int, set_.split(":"))
    total_min = (set_h * 60 + set_m) - (rise_h * 60 + rise_m)
    return f"{total_min // 60}:{total_min % 60:02d}"


def format_sun_text(t: dict) -> str:
    """One-line summary: rise/azimuth, transit/altitude, set/azimuth, daylight length."""
    return (
        f"出:{t['SunRiseTime']}/{t['SunRiseAZ']},"
        f"中:{t['SunTransitTime']}/{t['SunTransitAlt']},"
        f"沒:{t['SunSetTime']}/{t['SunSetAZ']}"
        f" ({_daylight(t['SunRiseTime'], t['SunSetTime'])})"
    )


if __name__ == "__main__":
    import sys

    county = sys.argv[1] if len(sys.argv) > 1 else "臺北市"
    if len(sys.argv) > 2:
        day = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    else:
        day = datetime.now(ZoneInfo("Asia/Taipei")).date()

    record = get_sun_times(county, day)
    print(f"{county} {record['Date']}")
    print(format_sun_text(record))
