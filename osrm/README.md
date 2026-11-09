# osrm

Driving time from one place to many, with the public
[OSRM](https://project-osrm.org/) demo server. **No API key required**: it is
keyless, and it sends `Access-Control-Allow-Origin: *` on successes *and* on
errors, so a static page can call it straight from the browser.

**API reference:
<https://project-osrm.org/docs/v5.24.0/api/#table-service>** — the `/table`
service used here; `/route` is the same server for a single path with geometry.

**Live demo:** https://jiechau.github.io/code_snippet_life/osrm/

- [osrm travel time](https://jiechau.github.io/code_snippet_life/osrm/osrm_travel_time.html)
  — a start `lat,lon` in, driving time to every saved spot in `places.js` out.

This folder holds **no script**, only the demo page: the call is one keyless `GET`.

## The call

One origin, many destinations, **one request**:

```
GET https://router.project-osrm.org/table/v1/driving/
      121.592399,25.070602;121.202497,25.103362;120.770338,24.647973
      ?sources=0&annotations=duration,distance
```

- Coordinates are **`lon,lat`**, the reverse of `places.js` and every location
  box in this repo. Getting it backwards is the most common mistake.
- `sources=0` makes the first coordinate the only start, so the answer is one
  row: `durations[0][i]` seconds and `distances[0][i]` metres to coordinate `i`.
- `destinations[i].distance` is how far OSRM moved point `i` to reach a road.
  The page flags anything over 300 m (the last stretch isn't counted) and
  anything over 5 km (it isn't the same place any more).
- `driving` is the only profile on the demo server, and it accepts no
  `exclude=` (no avoiding tolls, motorways or ferries): every flag answers
  `InvalidValue`.

## Usage policy

The demo server is [fair use](https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server):
no published quota, about **1 request a second**, no uptime guarantee, and it
blocks clients that hurt its stability. The page makes one request per Fetch,
including one on load. A browser can't set its own `User-Agent`, so the page
can't identify itself the way the policy asks a script to. For regular or bulk
use, self-host OSRM with Geofabrik's Taiwan extract.

## What the numbers are

Free-flow times on OpenStreetMap roads: **no live traffic**, so holiday 國五 and
city traffic don't show. Speeds come from road type, so mountain roads come out
optimistic (拉拉山 1h26m and 合歡山 3h29m from 內湖 are well under what you'd
actually drive). Islands are the other trap: 柚子湖 is on 綠島, whose roads OSRM
won't snap to, so the point moves ~35 km to the Taiwan coast and the time is to
there. The ferry isn't included.

For traffic-aware times, the keyed options are Google Routes (Compute Route
Matrix) and Mapbox (`driving-traffic`).
