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


def _order_key(hhmm: str) -> str:
    """
    A comparison key for a transit or set time within one day's record.

    "00:00" becomes "24:00"; everything else is returned unchanged. A transit or
    set that CWA stamps 00:00 is the rounding of 23:59:xx on that date -- the end
    of the day, not its start -- but compared as a string "00:00" sorts before
    every other time, which sends the branching below off to borrow the event
    from a neighbouring day that has none. Two real cases in three years:
    澎湖縣 2025-07-10 (transit 00:00) and 連江縣 2027-02-13 (set 00:00).

    Deliberately not applied to the rise: a rise at 00:00 really is just after
    midnight (six of them in the same three years), and normalising it would
    misorder the cycle the other way.
    """
    return "24:00" if hhmm == "00:00" else hhmm


def pick_moon_events(times: list[dict]) -> tuple[tuple, tuple, tuple]:
    """
    Pick the rise/transit/set of the moon cycle that starts on the target day.

    times = [yesterday, today, tomorrow]. Each returned event is a
    (day_label, time, angle) tuple where day_label is "" for today,
    "昨" for yesterday, "明" for tomorrow.

    An event can come back with an empty time when CWA has none to give: it
    publishes an occasional wholly blank record (all three times empty, the
    angles still filled in), about once a synodic month at 澎湖縣, and very
    rarely two consecutive days with no rise. Nothing in a 3-day window can
    recover those, so they travel as "" and format_moon_text() prints them as
    "–" rather than inventing a time.
    """
    t0, t1, t2 = times
    rise1 = t1["MoonRiseTime"]
    tran1 = t1["MoonTransitTime"]
    set1 = t1["MoonSetTime"]
    # Ordering only -- the values stored in the returned tuples stay as CWA sent
    # them, so a 00:00 still prints as 00:00.
    tran_k = _order_key(tran1)
    set_k = _order_key(set1)

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
    elif rise1 > tran_k:
        # Today's transit/set belong to the cycle that rose yesterday;
        # the cycle rising today transits and sets tomorrow.
        rise = ("", rise1, t1["MoonRiseAZ"])
        tran = ("明", t2["MoonTransitTime"], t2["MoonTransitAlt"])
        sett = ("明", t2["MoonSetTime"], t2["MoonSetAZ"])
    elif tran_k <= set_k:
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


MISSING = "–"  # an event CWA published no time for


def _moon_up(rise: str, set_: str) -> str:
    """
    Time the moon is up between two HH:MM times (may wrap past midnight), as H:MM.

    Either time may be "" when CWA published none -- see pick_moon_events() --
    in which case there is no span to state and this returns "–". It used to
    raise ValueError out of int("") there, which took the whole script down on
    about one day a month at 澎湖縣.
    """
    if not rise or not set_:
        return MISSING
    rise_h, rise_m = map(int, rise.split(":"))
    set_h, set_m = map(int, set_.split(":"))
    total_min = (set_h * 60 + set_m) - (rise_h * 60 + rise_m)
    if total_min < 0:
        total_min += 1440
    return f"{total_min // 60}:{total_min % 60:02d}"


def _format_event(label: str, event: tuple) -> str:
    """One "出:16:35/115" field, or "出:–" when CWA published no time for it."""
    day, time, angle = event
    return f"{label}:{day}{time}/{angle}" if time else f"{label}:{MISSING}"


def format_moon_text(rise: tuple, tran: tuple, sett: tuple) -> str:
    """One-line summary: rise/azimuth, transit/altitude, set/azimuth, time up."""
    return (
        f"{_format_event('出', rise)},"
        f"{_format_event('中', tran)},"
        f"{_format_event('沒', sett)}"
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
