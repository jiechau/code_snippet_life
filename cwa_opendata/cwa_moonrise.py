# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "pyyaml",
# ]
# ///
#
# uv run cwa_moonrise.py
# or
# uv run cwa_moonrise.py 高雄市
# or
# uv run cwa_moonrise.py 高雄市 2026-07-15

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

# A-B0063-001: daily moonrise / moon transit / moonset times per county
DATASET_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0063-001"


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


def get_moon_times(county: str, day: date, timeout: int = 15) -> list[dict]:
    """
    Fetch moonrise/transit/moonset data for a Taiwan county, covering a
    3-day window: [day-1, day, day+1].

    The moon rises ~50 minutes later each day, so on any given date one of
    rise/transit/set may be missing (empty string) or belong to the previous
    or next calendar day. The 3-day window lets pick_moon_events() stitch a
    full rise→transit→set cycle together.

    Returns the three raw daily records; each looks like:
      {"Date": "2026-07-15",
       "MoonRiseTime": "05:14", "MoonRiseAZ": "64.66",
       "MoonTransitTime": "11:58", "MoonTransitAlt": "84.51",
       "MoonSetTime": "18:43", "MoonSetAZ": "295.39", ...}
    """
    params = {
        "Authorization": CWA_API_KEY,
        "format": "JSON",
        "CountyName": county,
        "timeFrom": (day - timedelta(days=1)).isoformat(),
        "timeTo": (day + timedelta(days=2)).isoformat(),
        "sort": "Date",
    }
    resp = _session().get(DATASET_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    times = data["records"]["locations"]["location"][0]["time"]
    return times[:3]


def pick_moon_events(times: list[dict]) -> tuple[tuple, tuple, tuple]:
    """
    Pick the rise/transit/set of the moon cycle that starts on the target day.

    times = [yesterday, today, tomorrow]. Each returned event is a
    (day_label, time, angle) tuple where day_label is "" for today,
    "昨" for yesterday, "明" for tomorrow.
    """
    t0, t1, t2 = times
    rise1 = t1["MoonRiseTime"]
    tran1 = t1["MoonTransitTime"]
    set1 = t1["MoonSetTime"]

    if rise1 == "":
        # No rise today: the moon rose yesterday, transit/set happen today.
        rise = ("昨", t0["MoonRiseTime"], t0["MoonRiseAZ"])
        tran = ("", tran1, t1["MoonTransitAlt"])
        sett = ("", set1, t1["MoonSetAZ"])
    elif tran1 == "":
        # No transit today: transit and set slip to tomorrow.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("明", t2["MoonTransitTime"], t2["MoonTransitAlt"])
        sett = ("明", t2["MoonSetTime"], t2["MoonSetAZ"])
    elif set1 == "":
        # No set today: set slips to tomorrow.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("", tran1, t1["MoonTransitAlt"])
        sett = ("明", t2["MoonSetTime"], t2["MoonSetAZ"])
    elif rise1 > tran1:
        # Today's transit/set belong to the cycle that rose yesterday;
        # the cycle rising today transits and sets tomorrow.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("明", t2["MoonTransitTime"], t2["MoonTransitAlt"])
        sett = ("明", t2["MoonSetTime"], t2["MoonSetAZ"])
    elif tran1 <= set1:
        # Normal day: rise, transit and set all fall on the target day.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("", tran1, t1["MoonTransitAlt"])
        sett = ("", set1, t1["MoonSetAZ"])
    else:
        # Set crosses midnight into tomorrow.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("", tran1, t1["MoonTransitAlt"])
        sett = ("明", t2["MoonSetTime"], t2["MoonSetAZ"])
    return rise, tran, sett


def _moon_up(rise: str, set_: str) -> str:
    """Time the moon is up between two HH:MM times (may wrap past midnight), as H:MM."""
    rise_h, rise_m = map(int, rise.split(":"))
    set_h, set_m = map(int, set_.split(":"))
    total_min = (set_h * 60 + set_m) - (rise_h * 60 + rise_m)
    if total_min < 0:
        total_min += 1440
    return f"{total_min // 60}:{total_min % 60:02d}"


def format_moon_text(rise: tuple, tran: tuple, sett: tuple) -> str:
    """One-line summary: rise/azimuth, transit/altitude, set/azimuth, time up."""
    return (
        f"出:{rise[0]}{rise[1]}/{rise[2]},"
        f"中:{tran[0]}{tran[1]}/{tran[2]},"
        f"沒:{sett[0]}{sett[1]}/{sett[2]}"
        f" ({_moon_up(rise[1], sett[1])})"
    )


if __name__ == "__main__":
    import sys

    county = sys.argv[1] if len(sys.argv) > 1 else "臺北市"
    if len(sys.argv) > 2:
        day = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    else:
        day = datetime.now(ZoneInfo("Asia/Taipei")).date()

    times = get_moon_times(county, day)
    rise, tran, sett = pick_moon_events(times)
    print(f"{county} {times[1]['Date']}")
    print(format_moon_text(rise, tran, sett))
