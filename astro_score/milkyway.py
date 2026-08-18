# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
#
# uv run milkyway.py
# or
# uv run milkyway.py 24.1375,121.2745
# or
# uv run milkyway.py 24.1375,121.2745 3
#
# Scores how suitable each hour of the next N days is for Milky Way
# astrophotography at a GPS location, combining Open-Meteo cloud/moisture
# forecasts (multi-model ensemble) with locally computed astronomy:
# astronomical darkness, galactic core altitude, and moon interference.
#
# API reference: https://open-meteo.com/en/docs -- source for the hourly variable
# names in HOURLY_VARS and the model ids in MODELS. It does not cover the
# astronomy: sun/moon altitude and galactic core position are computed here,
# since the API offers only sunrise/sunset and daily=moon_phase.

import math
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Numerical weather models queried as an ensemble. Their disagreement is the
# confidence signal: four models predicting 10% cloud is a very different
# forecast from two predicting 0% and two predicting 60%. Who runs them, at what
# resolution, how independent they really are and why they are weighted equally:
# see "The four models" in README.md.
MODELS = ["icon_global", "jma_seamless", "gfs_global", "ecmwf_ifs025"]

# Not every model publishes every variable through Open-Meteo: of the four
# models here, only gfs_global returns visibility (icon_global, jma_seamless and
# ecmwf_ifs025 are all null), and precipitation_probability is null for
# jma_seamless. Missing values fall back to the ensemble mean (see _hour_vars).
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

# Galactic center, J2000: RA 17h45m40.04s, Dec -29deg00'28". Precession since
# J2000 moves this by well under a degree, far below the accuracy of the
# low-precision moon series below, so J2000 coordinates are used as-is.
GC_RA = 266.41683
GC_DEC = -29.00781

MOON_PHASE_NAMES = [
    # (max illuminated fraction, waxing name, waning name)
    (0.02, "新月", "新月"),
    (0.20, "眉月", "殘月"),
    (0.40, "眉月", "殘月"),
    (0.60, "上弦", "下弦"),
    (0.85, "盈凸", "虧凸"),
    (0.98, "盈凸", "虧凸"),
    (1.01, "滿月", "滿月"),
]

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


# --------------------------------------------------------------------------
# Astronomy: low-precision solar/lunar positions (Meeus, "Astronomical
# Algorithms"). Sun is good to ~0.01 deg, moon to ~0.3 deg in longitude --
# far more than enough to decide "is it dark" and "is the moon up".
# --------------------------------------------------------------------------


def julian_day(dt_utc: datetime) -> float:
    """Julian Day for a timezone-aware UTC datetime."""
    y, m = dt_utc.year, dt_utc.month
    day = (
        dt_utc.day
        + (dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600) / 24
    )
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + day
        + b
        - 1524.5
    )


def _obliquity(jd: float) -> float:
    """Mean obliquity of the ecliptic, in degrees."""
    return 23.439291 - 0.0130042 * ((jd - 2451545.0) / 36525)


def _ecliptic_to_equatorial(lon: float, lat: float, eps: float) -> tuple[float, float]:
    """Ecliptic (lon, lat) in degrees -> (RA, Dec) in degrees."""
    lon_r, lat_r, eps_r = map(math.radians, (lon, lat, eps))
    x = math.cos(lat_r) * math.cos(lon_r)
    y = (
        math.cos(eps_r) * math.cos(lat_r) * math.sin(lon_r)
        - math.sin(eps_r) * math.sin(lat_r)
    )
    z = (
        math.sin(eps_r) * math.cos(lat_r) * math.sin(lon_r)
        + math.cos(eps_r) * math.sin(lat_r)
    )
    ra = math.degrees(math.atan2(y, x)) % 360
    dec = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    return ra, dec


def sun_position(jd: float) -> tuple[float, float, float]:
    """Solar (RA, Dec, ecliptic longitude), all in degrees."""
    n = jd - 2451545.0
    mean_lon = (280.460 + 0.9856474 * n) % 360
    mean_anom = math.radians((357.528 + 0.9856003 * n) % 360)
    ecl_lon = (
        mean_lon
        + 1.915 * math.sin(mean_anom)
        + 0.020 * math.sin(2 * mean_anom)
    ) % 360
    ra, dec = _ecliptic_to_equatorial(ecl_lon, 0.0, _obliquity(jd))
    return ra, dec, ecl_lon


def moon_position(jd: float) -> tuple[float, float, float, float]:
    """Lunar (RA, Dec, distance in km, ecliptic longitude), degrees / km."""
    t = (jd - 2451545.0) / 36525
    # Mean elements.
    lp = (218.3164477 + 481267.88123421 * t) % 360     # mean longitude
    d = math.radians((297.8501921 + 445267.1114034 * t) % 360)   # elongation
    m = math.radians((357.5291092 + 35999.0502909 * t) % 360)    # sun anomaly
    mp = math.radians((134.9633964 + 477198.8675055 * t) % 360)  # moon anomaly
    f = math.radians((93.2720950 + 483202.0175233 * t) % 360)    # arg latitude

    ecl_lon = (
        lp
        + 6.289 * math.sin(mp)
        + 1.274 * math.sin(2 * d - mp)
        + 0.658 * math.sin(2 * d)
        + 0.214 * math.sin(2 * mp)
        - 0.186 * math.sin(m)
        - 0.114 * math.sin(2 * f)
        + 0.059 * math.sin(2 * d - 2 * mp)
        + 0.057 * math.sin(2 * d - m - mp)
        + 0.053 * math.sin(2 * d + mp)
        + 0.046 * math.sin(2 * d - m)
        - 0.041 * math.sin(m - mp)
        - 0.035 * math.sin(d)
        - 0.031 * math.sin(m + mp)
    ) % 360
    ecl_lat = (
        5.128 * math.sin(f)
        + 0.281 * math.sin(mp + f)
        - 0.278 * math.sin(f - mp)
        - 0.173 * math.sin(2 * d - f)
        + 0.055 * math.sin(2 * d + f - mp)
        - 0.046 * math.sin(2 * d - f - mp)
        + 0.033 * math.sin(2 * d + f)
        + 0.017 * math.sin(2 * mp + f)
    )
    dist = (
        385000.56
        - 20905.355 * math.cos(mp)
        - 3699.111 * math.cos(2 * d - mp)
        - 2955.968 * math.cos(2 * d)
        - 569.925 * math.cos(2 * mp)
    )
    ra, dec = _ecliptic_to_equatorial(ecl_lon, ecl_lat, _obliquity(jd))
    return ra, dec, dist, ecl_lon


def local_sidereal_time(jd: float, lon_deg: float) -> float:
    """Local apparent sidereal time in degrees."""
    t = (jd - 2451545.0) / 36525
    gmst = (
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * t * t
    )
    return (gmst + lon_deg) % 360


def alt_az(ra: float, dec: float, lat: float, lst: float) -> tuple[float, float]:
    """Equatorial (RA, Dec) -> (altitude, azimuth from north), degrees."""
    ha = math.radians((lst - ra) % 360)
    dec_r, lat_r = math.radians(dec), math.radians(lat)
    sin_alt = (
        math.sin(lat_r) * math.sin(dec_r)
        + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha)
    )
    alt = math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))
    az = math.degrees(
        math.atan2(
            -math.cos(dec_r) * math.sin(ha),
            math.sin(dec_r) * math.cos(lat_r)
            - math.sin(lat_r) * math.cos(dec_r) * math.cos(ha),
        )
    ) % 360
    return alt, az


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Great-circle angle between two equatorial positions, in degrees."""
    d1, d2 = math.radians(dec1), math.radians(dec2)
    dra = math.radians(ra1 - ra2)
    cos_sep = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(dra)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_sep))))


def moon_illumination(
    sun_ra: float, sun_dec: float, moon_ra: float, moon_dec: float, moon_dist: float
) -> float:
    """Illuminated fraction of the lunar disk, 0..1."""
    elong = math.radians(angular_separation(sun_ra, sun_dec, moon_ra, moon_dec))
    au_km = 149_597_870.7
    # Phase angle of the moon as seen from Earth (Meeus 48.2).
    phase = math.atan2(
        au_km * math.sin(elong), moon_dist - au_km * math.cos(elong)
    )
    return (1 + math.cos(phase)) / 2


def moon_phase_name(illum: float, sun_ecl_lon: float, moon_ecl_lon: float) -> str:
    """Chinese phase name; waxing/waning from the moon-sun elongation."""
    waxing = (moon_ecl_lon - sun_ecl_lon) % 360 < 180
    for limit, wax_name, wane_name in MOON_PHASE_NAMES:
        if illum < limit:
            return wax_name if waxing else wane_name
    return "滿月"


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def ramp(x: float, lo: float, hi: float) -> float:
    """Smooth 0->1 ramp: 0 at or below lo, 1 at or above hi."""
    if hi == lo:
        return 1.0 if x >= hi else 0.0
    t = min(1.0, max(0.0, (x - lo) / (hi - lo)))
    return t * t * (3 - 2 * t)


def astronomy_gates(
    dt_utc: datetime, lat: float, lon: float
) -> dict:
    """
    Astronomy terms for one instant. These are hard gates: if the sky isn't
    astronomically dark, or the galactic core is below the horizon, no weather
    forecast can rescue the hour.
    """
    jd = julian_day(dt_utc)
    lst = local_sidereal_time(jd, lon)

    sun_ra, sun_dec, sun_ecl = sun_position(jd)
    sun_alt, _ = alt_az(sun_ra, sun_dec, lat, lst)

    moon_ra, moon_dec, moon_dist, moon_ecl = moon_position(jd)
    moon_alt, _ = alt_az(moon_ra, moon_dec, lat, lst)
    illum = moon_illumination(sun_ra, sun_dec, moon_ra, moon_dec, moon_dist)

    gc_alt, gc_az = alt_az(GC_RA, GC_DEC, lat, lst)

    # Astronomical twilight: useless above -12 deg, fully dark below -18.
    darkness = 1.0 - ramp(sun_alt, -18.0, -12.0)

    # The core needs real altitude -- near the horizon it is buried in airmass,
    # extinction and ground-level light pollution.
    core_up = ramp(gc_alt, 0.0, 25.0)

    # Moon glare scales with illuminated fraction and how high it sits. A
    # brilliant moon still low or below the horizon costs little; the sqrt-ish
    # exponent reflects that even a half moon washes out the core badly.
    glare = illum**0.6 * ramp(moon_alt, -8.0, 12.0)
    # A moon on the far side of the sky from the core is somewhat less harmful.
    sep = angular_separation(moon_ra, moon_dec, GC_RA, GC_DEC)
    glare *= 1 - 0.25 * (sep / 180)
    moon_free = 1 - 0.95 * glare

    return {
        "darkness": darkness,
        "core_up": core_up,
        "moon_free": moon_free,
        "sun_alt": sun_alt,
        "moon_alt": moon_alt,
        "moon_illum": illum,
        "moon_phase": moon_phase_name(illum, sun_ecl, moon_ecl),
        "gc_alt": gc_alt,
        "gc_az": gc_az,
        "gates": darkness * core_up * moon_free,
    }


def sky_quality(v: dict) -> float:
    """
    Weather term, 0..1, for one model's forecast of one hour.

    Cloud layers are treated as independent screens: low cloud blocks
    completely, mid cloud nearly so, and high cirrus -- which forecasters
    often shrug at -- still robs the core of contrast, so it carries real
    weight. The reported total cloud cover acts as a floor so an optimistic
    layer breakdown cannot talk the score up.
    """
    low = (v.get("cloud_cover_low") or 0) / 100
    mid = (v.get("cloud_cover_mid") or 0) / 100
    high = (v.get("cloud_cover_high") or 0) / 100
    total = (v.get("cloud_cover") or 0) / 100
    screens = 1 - (1 - low) * (1 - 0.85 * mid) * (1 - 0.70 * high)
    # Total cover is only a floor, deliberately discounted: taking it at face
    # value would re-charge full weight for cirrus that the layer weighting
    # just discounted on purpose.
    obstruction = max(screens, 0.75 * total)
    clear = (1 - obstruction) ** 1.3

    pp = v.get("precipitation_probability")
    precip = 1 - 0.9 * (pp / 100) ** 1.2 if pp is not None else 1.0

    # Temperature/dew-point spread: a small spread means fog, haze and dew
    # forming on the front element -- the classic ruined-session cause.
    temp, dew = v.get("temperature_2m"), v.get("dew_point_2m")
    if temp is not None and dew is not None:
        spread = 0.35 + 0.65 * ramp(temp - dew, 0.0, 5.0)
    else:
        spread = 1.0

    rh = v.get("relative_humidity_2m")
    humid = 1 - 0.4 * max(0.0, (rh - 85) / 15) if rh is not None else 1.0

    vis = v.get("visibility")
    # Of the four models only gfs_global reports visibility, so for the other
    # three this is the ensemble mean (i.e. gfs alone); absent means neutral.
    # It is a ground-level measure -- haze and mist, not upper-air transparency
    # -- and it saturates at 24140 m (15 miles, the unit gfs reports it in).
    transparency = 0.5 + 0.5 * ramp(vis / 1000, 5.0, 20.0) if vis else 1.0

    wind = v.get("wind_speed_10m")
    if wind is not None:
        # Strong wind shakes a tripod through a 20 s exposure; dead calm with
        # saturated air is how valleys fog in.
        shake = 1 - 0.35 * ramp(wind, 30.0, 60.0)
        stagnation = 0.9 if (wind < 3 and (rh or 0) > 88) else 1.0
        breeze = shake * stagnation
    else:
        breeze = 1.0

    return clear * precip * spread * humid * transparency * breeze


# --------------------------------------------------------------------------
# Open-Meteo
# --------------------------------------------------------------------------


def fetch_forecast(lat: float, lon: float, days: int, timeout: int = 30) -> dict:
    """
    Hourly multi-model forecast. No API key: Open-Meteo's free tier allows
    10,000 calls/day (600/min) for non-commercial use, and one request of this
    shape (10 variables x 4 models) bills as a few fractional calls.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "models": ",".join(MODELS),
        "timezone": "auto",
        "forecast_days": days,
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    # Open-Meteo only suffixes variable names when several models are
    # requested; ask for a single model and the keys come back bare. A model
    # that simply does not publish a variable still returns the key full of
    # nulls, so a genuinely missing key means the response shape is not what
    # _hour_vars expects -- which would otherwise degrade silently into every
    # variable reading as None, i.e. a perfect sky at every hour.
    hourly = data.get("hourly", {})
    missing = [
        f"{var}_{model}"
        for model in MODELS
        for var in HOURLY_VARS
        if f"{var}_{model}" not in hourly
    ]
    if missing:
        raise SystemExit(
            f"Unexpected response shape, {len(missing)} series missing "
            f"(e.g. {missing[0]}). MODELS needs at least two entries, and each "
            f"id must be one Open-Meteo currently serves."
        )
    return data


def _hour_vars(hourly: dict, i: int) -> dict[str, dict]:
    """
    Per-model variables for hour i, with gaps filled from the ensemble.

    Open-Meteo suffixes every series with its model name. Where a model does
    not publish a variable at all (visibility, precipitation probability) the
    mean of the models that do is substituted, so one model's silence does not
    make it look artificially clear.
    """
    per_model: dict[str, dict] = {m: {} for m in MODELS}
    for var in HOURLY_VARS:
        values = {}
        for m in MODELS:
            series = hourly.get(f"{var}_{m}")
            values[m] = series[i] if series and i < len(series) else None
        present = [x for x in values.values() if x is not None]
        fallback = sum(present) / len(present) if present else None
        for m in MODELS:
            per_model[m][var] = values[m] if values[m] is not None else fallback
    return per_model


def score_hours(data: dict, lat: float, lon: float) -> list[dict]:
    """
    Score every future forecast hour, including the ones no camera would ever
    use. Hours that fail the astronomy gates score 0 and are marked not
    shootable, but they keep their weather values so the hourly grid can show
    a continuous 24-hour series.
    """
    hourly = data["hourly"]
    tz = timezone(timedelta(seconds=data["utc_offset_seconds"]))
    # forecast_days starts the series at 00:00 local, so the first hours are
    # already in the past. Keep the hour in progress, drop the rest.
    cutoff = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
    scored = []

    for i, stamp in enumerate(hourly["time"]):
        local = datetime.fromisoformat(stamp).replace(tzinfo=tz)
        if local < cutoff:
            continue
        astro = astronomy_gates(local.astimezone(timezone.utc), lat, lon)

        per_model = _hour_vars(hourly, i)
        model_scores = {
            m: astro["gates"] * sky_quality(v) for m, v in per_model.items()
        }
        values = list(model_scores.values())
        scored.append(
            {
                "local": local,
                "astro": astro,
                "per_model": per_model,
                "model_scores": model_scores,
                "score": sum(values) / len(values),
                "spread": max(values) - min(values),
                "shootable": astro["gates"] > 0.001,
                "lead_days": (local - cutoff).total_seconds() / 86400,
                "clouds": {
                    key: _mean(
                        [v[key] for v in per_model.values() if v[key] is not None]
                    )
                    for key in ("cloud_cover", "cloud_cover_low",
                                "cloud_cover_mid", "cloud_cover_high")
                },
                "precip": _mean(
                    [
                        v["precipitation_probability"]
                        for v in per_model.values()
                        if v["precipitation_probability"] is not None
                    ]
                ),
                "spread_c": _mean(
                    [
                        v["temperature_2m"] - v["dew_point_2m"]
                        for v in per_model.values()
                        if v["temperature_2m"] is not None
                        and v["dew_point_2m"] is not None
                    ]
                ),
            }
        )
    return scored


def _mean(values: list) -> float | None:
    return sum(values) / len(values) if values else None


def group_by_night(scored: list[dict]) -> list[tuple[str, list[dict]]]:
    """
    Group hours into nights. Hours before noon belong to the previous
    evening's session, so a 01:00 shot is filed under the night it started.
    """
    nights: dict[str, list[dict]] = {}
    for entry in scored:
        local = entry["local"]
        night = local.date() if local.hour >= 12 else local.date() - timedelta(days=1)
        nights.setdefault(night.isoformat(), []).append(entry)
    return sorted(nights.items())


def night_of(local: datetime) -> str:
    """ISO date of the night a local timestamp belongs to."""
    d = local.date() if local.hour >= 12 else local.date() - timedelta(days=1)
    return d.isoformat()


def group_by_day(scored: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group hours by calendar day, for the full 24-hour grid."""
    days: dict[str, list[dict]] = {}
    for entry in scored:
        days.setdefault(entry["local"].date().isoformat(), []).append(entry)
    return sorted(days.items())


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def _display_width(s: str) -> int:
    """Terminal columns a string occupies; CJK characters take two."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s: str, width: int, right: bool = False) -> str:
    """Pad to a column width, counting CJK characters as double-width."""
    fill = " " * max(0, width - _display_width(s))
    return fill + s if right else s + fill


def row(cells: list[tuple[str, int, bool]]) -> str:
    """Render one table row from (text, width, right_align) cells."""
    return ("  " + " ".join(pad(text, w, right) for text, w, right in cells)).rstrip()


def confidence_label(entry: dict) -> str:
    """
    How much to trust the score, kept as a separate axis from the score
    itself. Two things erode it: the models disagreeing with each other, and
    forecast lead time -- a unanimous 90% six days out is still a guess.
    """
    lead_penalty = 0.5 * ramp(entry["lead_days"], 1.5, 6.0)
    uncertainty = max(entry["spread"], lead_penalty)
    if uncertainty < 0.10:
        return "高"
    if uncertainty < 0.25:
        return "中"
    return "低"


def night_label(iso_date: str) -> str:
    d = datetime.fromisoformat(iso_date).date()
    return f"{d.month:02d}/{d.day:02d}({WEEKDAYS[d.weekday()]})"


def verdict(score: float) -> str:
    if score >= 0.60:
        return "值得出門"
    if score >= 0.40:
        return "可以一試"
    if score >= 0.20:
        return "機會不大"
    return "不建議"


GRID_LABEL_WIDTH = 7
GRID_COL_WIDTH = 5


def _cell(value: float | None, fmt: str = ".0f", unit: str = "") -> str:
    """One grid cell; a dash where the models supplied nothing."""
    return "-" if value is None else f"{value:{fmt}}{unit}"


def _score_cell(score: float, shootable: bool, unit: str = "") -> str:
    """
    A score cell, distinguishing two kinds of zero: an hour the astronomy
    gates shut outright (daylight, core below the horizon) is a hard 0, while
    a dark hour ruined by moon and cloud can round to 0 from a real value.
    Showing the latter as "<1" keeps an impossible hour and a merely hopeless
    one from looking identical.
    """
    pct = score * 100
    if shootable and 0 < pct < 0.5:
        return f"<1{unit}"
    return f"{pct:.0f}{unit}"


def print_day_grid(iso_date: str, entries: list[dict], best: dict | None) -> None:
    """
    Hour-by-hour grid for one calendar day, one column per hour -- the layout
    the stargazing apps use. Daylight hours are included so the weather series
    is continuous; they simply score 0, since the astronomy gates shut them.
    Each model's own score gets its own row at the bottom, so disagreement
    stays visible instead of being averaged away.
    """

    def line(label: str, cells: list[str]) -> str:
        return (
            pad(label, GRID_LABEL_WIDTH)
            + "".join(pad(c, GRID_COL_WIDTH, right=True) for c in cells)
        ).rstrip()

    d = datetime.fromisoformat(iso_date).date()
    header = f"{d.month:02d}/{d.day:02d}({WEEKDAYS[d.weekday()]}) 逐時"
    if best is not None and best["local"].date() == d:
        header += f"  ★ 最佳 {best['local']:%H:%M}"
    print(header)

    # A dot marks the hours that clear the astronomy gates -- the only ones
    # where the score means anything.
    print(line("時間", [f"{e['local']:%H}" for e in entries]))
    if any(e["shootable"] for e in entries):
        print(line("", ["·" if e["shootable"] else "" for e in entries]))
    print(line("機率", [_score_cell(e["score"], e["shootable"], "%") for e in entries]))
    print(
        line(
            "信心",
            [confidence_label(e) if e["shootable"] else "-" for e in entries],
        )
    )
    print(line("銀心", [f"{e['astro']['gc_alt']:.0f}°" for e in entries]))
    print(
        line(
            "月亮",
            [
                f"{e['astro']['moon_alt']:.0f}°" if e["astro"]["moon_alt"] > -8 else "落"
                for e in entries
            ],
        )
    )
    print(line("太陽", [f"{e['astro']['sun_alt']:.0f}°" for e in entries]))
    for label, key in [
        ("雲量", "cloud_cover"),
        ("高雲", "cloud_cover_high"),
        ("中雲", "cloud_cover_mid"),
        ("低雲", "cloud_cover_low"),
    ]:
        print(line(label, [_cell(e["clouds"][key]) for e in entries]))
    print(line("降雨", [_cell(e["precip"], unit="%") for e in entries]))
    print(line("露點差", [_cell(e["spread_c"], ".1f") for e in entries]))
    for model in MODELS:
        print(
            line(
                model.split("_")[0],
                [
                    _score_cell(e["model_scores"][model], e["shootable"])
                    for e in entries
                ],
            )
        )


def print_all_grids(scored: list[dict], best: dict | None) -> None:
    """Full 24-hour grid for every forecast day."""
    print()
    print("逐時預報 (· = 通過天文條件的時段)")
    for iso_date, entries in group_by_day(scored):
        print()
        print_day_grid(iso_date, entries, best)
    print()
    print(f"各模式 {' / '.join(m.split('_')[0] for m in MODELS)} 為該模式單獨評分")


def print_report(data: dict, lat: float, lon: float, days: int) -> None:
    scored = score_hours(data, lat, lon)

    print("銀河攝影條件評估")
    print(
        f"地點 {lat:.4f}, {lon:.4f}  海拔 {data['elevation']:.0f}m  "
        f"時區 {data['timezone']}  未來 {days} 天"
    )
    print(f"模式 {', '.join(MODELS)}")
    print("條件 天文暗夜(太陽 <-18°) × 銀心高度 × 月光 × 天氣")
    print()

    if not scored:
        print("沒有可用的預報資料。")
        return

    # The summary is grouped by night and only considers hours that clear the
    # astronomy gates; the grid below shows every hour of every day.
    shootable = [e for e in scored if e["shootable"]]
    if not shootable:
        print("這段期間銀心都在地平線下或天色未暗,沒有可拍攝的時段。")
        print("以下仍列出逐時天氣。")
        print()
        print_all_grids(scored, None)
        return

    nights = group_by_night(shootable)

    print("各夜最佳時段")
    print(
        row(
            [
                ("夜晚", 11, False),
                ("最佳", 5, False),
                ("機率", 5, True),
                ("信心", 4, False),
                ("月相", 10, False),
                ("銀心", 5, True),
                ("雲量 總(低/中/高)", 20, False),
                ("降雨", 4, True),
            ]
        )
    )
    best_overall = None
    for iso_date, rows in nights:
        best = max(rows, key=lambda r: r["score"])
        if best_overall is None or best["score"] > best_overall["score"]:
            best_overall = best
        c, astro = best["clouds"], best["astro"]
        print(
            row(
                [
                    (night_label(iso_date), 11, False),
                    (f"{best['local']:%H:%M}", 5, False),
                    (_score_cell(best["score"], True, "%"), 5, True),
                    (confidence_label(best), 4, False),
                    (
                        f"{astro['moon_phase']}{astro['moon_illum'] * 100:.0f}%",
                        10,
                        False,
                    ),
                    (f"{astro['gc_alt']:.0f}°", 5, True),
                    (
                        f"{c['cloud_cover']:.0f} "
                        f"({c['cloud_cover_low']:.0f}/{c['cloud_cover_mid']:.0f}/"
                        f"{c['cloud_cover_high']:.0f})",
                        20,
                        False,
                    ),
                    (f"{best['precip'] or 0:.0f}%", 4, True),
                ]
            )
        )

    print()
    top_iso = night_of(best_overall["local"])
    print(
        f"最佳時刻 {night_label(top_iso)} {best_overall['local']:%H:%M} "
        f"機率 {best_overall['score'] * 100:.0f}% "
        f"(信心 {confidence_label(best_overall)}) — "
        f"{verdict(best_overall['score'])}"
    )

    print_all_grids(scored, best_overall)


if __name__ == "__main__":
    # Taipei -- light-polluted, so a useful sanity check that the score is
    # driven by sky conditions rather than always reading high.
    location = sys.argv[1] if len(sys.argv) > 1 else "25.033,121.565"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7

    try:
        lat_s, lon_s = location.split(",")
        lat, lon = float(lat_s), float(lon_s)
    except ValueError:
        raise SystemExit(f'Bad location "{location}": expected "lat,lon"')

    print_report(fetch_forecast(lat, lon, days), lat, lon, days)
