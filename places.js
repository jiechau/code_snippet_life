/*
 * Saved stargazing spots, shared by every demo page in this repo.
 *
 * This is the one exception to the one-folder-per-snippet rule: the list used to
 * be copied verbatim into each page, which meant adding a spot was the same edit
 * made three times and easy to get half-done. It lives at the repo root so both
 * open_meteo/ and astro_score/ can reach it as "../places.js".
 *
 * Adding, removing or reordering a spot is a one-line change HERE and nowhere
 * else. The first entry is the default location, so reordering the list changes
 * what every page opens on.
 *
 * Loaded as a plain classic script (no type="module"), deliberately: modules are
 * fetched under CORS rules and would fail when a page is opened straight off
 * disk as file://, which the READMEs offer as a way to run these pages with no
 * server at all. A top-level `const` in a classic script is visible to the
 * inline <script> that follows it, so the pages just use PLACES directly.
 */
const PLACES = [
    ["輸入", 25.070602, 121.592399],
    ["瑞光路", 25.0781166, 121.5703769],
    ["大武崙砲台", 25.157534, 121.709982],
    ["內洞停車場", 24.8345551, 121.5264508],
    ["烏石港", 24.870683, 121.839613],
    ["東澳", 24.508322, 121.838141],
    ["石梯坪", 23.4913949, 121.4882516],
    ["加路蘭", 22.806095, 121.196973],
    ["龍磐公園", 21.922833, 120.8274758],
    ["拉拉山", 24.682179, 121.379457],
    ["合歡山", 24.1182852, 121.2350106],
    ["柚子湖", 22.6657971, 121.5086903],
];

/* The page's starting coordinates, taken from the first spot above. */
const [, DEFAULT_LAT, DEFAULT_LON] = PLACES[0];

/*
 * PLACES[0] is the one entry that is not a saved spot. 輸入 ("input") is
 * wherever the user is asking about right now: the coordinate typed into a
 * page's location box, or the device's own position after the 使用目前位置
 * button. Keeping it in this list rather than in a page is what gives it to the
 * page that has no location box -- astro-score_daily.html draws a row per
 * PLACES entry, so 輸入 is simply its first row, and pointing that row at where
 * you are standing needs no location field there at all.
 *
 * setInputPlace() mutates that entry in place, for this page load and no
 * longer: nothing is stored, so a reload is back to the coordinate written
 * above and what this file says is always what a fresh page opens on. That also
 * means the 輸入 pill built by buildPlaces() carries a stale coordinate
 * afterwards, so every caller rebuilds the pills.
 */
function setInputPlace(lat, lon) {
    PLACES[0][1] = lat;
    PLACES[0][2] = lon;
}

/*
 * getCurrentPosition()'s three failure codes, in the same "CJK, English in
 * parentheses" voice the pages use for anything a user reads.
 */
const GEO_ERRORS = {
    1: "定位被拒絕 (permission denied — needs https and your consent)",
    2: "取不到位置 (position unavailable)",
    3: "定位逾時 (timed out)",
};

/*
 * The device's own position as a promise of {lat, lon, accuracy}, rounded to 6
 * decimals (~0.1 m -- far finer than any forecast grid, and short enough to
 * read in a location box).
 *
 * Geolocation is a secure-context API: https:// and localhost are fine, so the
 * published Pages site is fine, but a page opened straight off disk as file://
 * is refused by most browsers -- the one thing on these pages that the READMEs'
 * "just open the file" route cannot do. That refusal arrives as an ordinary
 * rejection here, which is why every caller prints the message beside the
 * button instead of assuming the button always works.
 */
function currentPosition({ timeout = 10000, maximumAge = 60000 } = {}) {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("此瀏覽器不支援定位 (no navigator.geolocation)"));
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({
                lat: Number(pos.coords.latitude.toFixed(6)),
                lon: Number(pos.coords.longitude.toFixed(6)),
                accuracy: pos.coords.accuracy,
            }),
            (err) => reject(new Error(GEO_ERRORS[err.code] || err.message || "定位失敗")),
            { enableHighAccuracy: true, timeout, maximumAge },
        );
    });
}

/*
 * ---------------------------------------------------------------------------
 * 在地圖上點選 (pick on the map)
 * ---------------------------------------------------------------------------
 *
 * pickOnMap() opens a real, draggable map over the page and resolves to the
 * {lat, lon} under its crosshair, or to null if the user cancels. It is the
 * third way a location box gets filled, beside typing and 使用目前位置, and it
 * is the one that answers "somewhere over there" -- a ridge two valleys away
 * has coordinates nobody knows by heart.
 *
 * Three decisions worth knowing before touching it:
 *
 * 1. OpenStreetMap, not Google. Google's embed and JavaScript APIs both want a
 *    billing-enabled key, and a key in the source of a published static page is
 *    public the moment it ships -- the same wall cwa_opendata hits, but without
 *    cwa's way out, since the key would be ours and not the visitor's. OSM's
 *    standard tiles are keyless and CORS-clean, exactly like the other services
 *    these pages call. Attribution is required and is on the dialog; the tile
 *    server is a volunteer-funded courtesy, so this asks for the dozen or so
 *    tiles one screen needs and nothing more.
 *
 * 2. A dialog in this page, not another tab. A second window would need either
 *    a map page of its own at the repo root (nothing but this file lives there,
 *    deliberately) or a document written into about:blank, and would then have
 *    to hand the coordinate back across a popup blocker and a file:// origin
 *    that refuses to be scripted. An overlay has none of those problems and
 *    still opens, pins and closes exactly as asked.
 *
 * 3. No Leaflet, no map library. A slippy map is a Mercator formula, a grid of
 *    <img> tiles and a drag handler -- about 120 lines below -- and pulling a
 *    library off a CDN for it would be the first third-party script in the
 *    repo. It is the same call light_pollution makes when it decodes gzip with
 *    DecompressionStream instead of shipping pako.
 *
 * What you give up by hand-rolling it: no rotation, no fractional zoom (so a
 * pinch steps whole levels rather than scaling smoothly), no search box, no
 * marker layers. None of that helps you point at a hilltop.
 */

const MAP_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const MAP_TILE_SIZE = 256;          // px per tile, fixed by the tile scheme
const MAP_MIN_ZOOM = 2;             // below this the world is smaller than the view
const MAP_MAX_ZOOM = 19;            // the deepest zoom OSM renders
const MAP_START_ZOOM = 13;          // ~19 m per pixel: a valley, not a continent
const MAP_MAX_LAT = 85.05112878;    // where Mercator runs off to infinity
const MAP_DRAG_SLOP = 5;            // px of travel that makes a tap a drag instead
const MAP_PINCH_STEP = 1.6;         // finger spread that spends one zoom level

/* Web Mercator, in world pixels: the whole earth is 256 * 2^zoom px square,
 * x eastwards from 180°W, y southwards from the top. Every other bit of
 * geometry here is these four functions plus a subtraction. */
function mapClamp(value, lo, hi) { return Math.min(hi, Math.max(lo, value)); }
function mapWrapLon(lon) { return ((((lon + 180) % 360) + 360) % 360) - 180; }

function mapWorldX(lon, zoom) {
    return ((lon + 180) / 360) * MAP_TILE_SIZE * 2 ** zoom;
}
function mapWorldY(lat, zoom) {
    const phi = (mapClamp(lat, -MAP_MAX_LAT, MAP_MAX_LAT) * Math.PI) / 180;
    const y = (1 - Math.log(Math.tan(phi) + 1 / Math.cos(phi)) / Math.PI) / 2;
    return y * MAP_TILE_SIZE * 2 ** zoom;
}
function mapLonAt(x, zoom) {
    return (x / (MAP_TILE_SIZE * 2 ** zoom)) * 360 - 180;
}
function mapLatAt(y, zoom) {
    const t = Math.PI * (1 - (2 * y) / (MAP_TILE_SIZE * 2 ** zoom));
    return (Math.atan(Math.sinh(t)) * 180) / Math.PI;
}

/*
 * The dialog's stylesheet, injected once per page rather than copied into the
 * eleven pages' <style> blocks -- this is the one thing in the repo that draws
 * its own chrome, so its CSS travels with its code. Every colour falls back to
 * a literal, because the pages' custom properties are defined in the pages and
 * this file has to work when it is loaded by one that lacks them.
 */
function mapStyle() {
    if (document.getElementById("mapdlg-style")) return;
    const style = document.createElement("style");
    style.id = "mapdlg-style";
    style.textContent = `
        .mapdlg {
            position: fixed; inset: 0; z-index: 9999;
            display: flex; align-items: center; justify-content: center;
            background: rgba(0, 0, 0, 0.45); padding: 12px;
        }
        .mapdlg .mapcard {
            display: flex; flex-direction: column;
            width: min(760px, 96vw); max-height: 94vh; overflow: hidden;
            background: white; border-radius: 14px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: var(--fg, #333);
        }
        .mapdlg .maphead {
            display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap;
            padding: 12px 16px; border-bottom: 1px solid var(--line, #e3e6ea);
        }
        .mapdlg .maphead strong { font-size: 0.95rem; }
        .mapdlg .maphint { font-size: 0.8rem; color: var(--muted, #777); }
        /* touch-action: none, or a drag on a phone scrolls the page behind
           instead of panning the map. */
        .mapdlg .mapview {
            position: relative; flex: 1 1 auto; overflow: hidden;
            height: min(58vh, 460px); min-height: 220px;
            background: #dfe3e8; cursor: grab;
            touch-action: none; user-select: none;
        }
        .mapdlg .mapview.dragging { cursor: grabbing; }
        .mapdlg .maptile {
            position: absolute; width: ${MAP_TILE_SIZE}px; height: ${MAP_TILE_SIZE}px;
        }
        /* The crosshair: a ring with a dot in it, pinned to the exact centre of
           the view, which is the coordinate this dialog returns. Ringed in white
           as well as red so it stays visible over a dark forest tile. */
        .mapdlg .mappin {
            position: absolute; left: 50%; top: 50%;
            width: 26px; height: 26px; margin: -13px 0 0 -13px;
            border: 2px solid var(--err, #c0392b); border-radius: 50%;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.85),
                        inset 0 0 0 2px rgba(255, 255, 255, 0.85);
            pointer-events: none;
        }
        .mapdlg .mappin::after {
            content: ""; position: absolute; left: 50%; top: 50%;
            width: 4px; height: 4px; margin: -2px 0 0 -2px;
            border-radius: 50%; background: var(--err, #c0392b);
        }
        .mapdlg .mapzoom {
            position: absolute; right: 10px; top: 10px;
            display: flex; flex-direction: column; gap: 4px;
        }
        .mapdlg .mapzoom button {
            width: 32px; height: 32px; padding: 0;
            font: inherit; font-size: 1.1rem; font-weight: 700; line-height: 1;
            border: 1px solid var(--line, #e3e6ea); border-radius: 8px;
            background: rgba(255, 255, 255, 0.95); color: var(--fg, #333);
            cursor: pointer;
        }
        .mapdlg .mapzoom button:hover:not(:disabled) {
            background: white;
            border-color: var(--accent, #2196F3); color: var(--accent, #2196F3);
        }
        .mapdlg .mapzoom button:disabled { opacity: 0.4; cursor: default; }
        /* Required by the tile licence, and it has to stay on screen. */
        .mapdlg .mapattr {
            position: absolute; right: 0; bottom: 0;
            padding: 2px 6px; border-radius: 6px 0 0 0;
            background: rgba(255, 255, 255, 0.8);
            font-size: 0.7rem; color: var(--muted, #777);
        }
        .mapdlg .mapattr a { color: inherit; }
        .mapdlg .mapfoot {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
            padding: 12px 16px; border-top: 1px solid var(--line, #e3e6ea);
        }
        .mapdlg .mapcoord {
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.85rem;
        }
        .mapdlg .mapz { font-size: 0.8rem; color: var(--muted, #777); }
        /* The two buttons travel as a pair: on a phone the footer wraps, and
           margin-left auto on the pair (rather than a spacer between them) is
           what keeps 取消 and 確定 on one line together instead of stranding the
           primary action on a line of its own. */
        .mapdlg .mapbtns { display: flex; gap: 10px; margin-left: auto; }
        .mapdlg .mapfoot button {
            font: inherit; font-weight: 600; padding: 8px 18px;
            border: 2px solid var(--accent, #2196F3); border-radius: 8px;
            background: var(--accent, #2196F3); color: white; cursor: pointer;
        }
        .mapdlg .mapfoot button.cancel {
            background: white; color: var(--accent, #2196F3);
        }
    `;
    document.head.appendChild(style);
}

/*
 * Open the picker and resolve to {lat, lon} (6 decimals, like
 * currentPosition()) once 確定 is pressed, or to null on 取消, Escape or a
 * click on the backdrop. It never rejects: cancelling is an answer, and the
 * caller's job on null is to leave the page exactly as it was.
 *
 * The starting view is where the caller says, and anything non-finite there --
 * an empty location box, a half-typed coordinate -- falls back to
 * DEFAULT_LAT/DEFAULT_LON like every other reader of that box.
 *
 * Panning moves the map under a fixed crosshair rather than dropping a marker
 * where you tapped: on a phone a fingertip covers about a kilometre at these
 * zooms, and the thing you are aiming at would be under it. Tapping still
 * works -- it brings that point to the crosshair, where you can see it.
 */
function pickOnMap({ lat, lon, zoom } = {}) {
    mapStyle();

    let center = {
        lat: Number.isFinite(lat) ? mapClamp(lat, -MAP_MAX_LAT, MAP_MAX_LAT) : DEFAULT_LAT,
        lon: Number.isFinite(lon) ? mapWrapLon(lon) : DEFAULT_LON,
    };
    let z = mapClamp(Number.isFinite(zoom) ? Math.round(zoom) : MAP_START_ZOOM,
                     MAP_MIN_ZOOM, MAP_MAX_ZOOM);

    const dlg = document.createElement("div");
    dlg.className = "mapdlg";
    dlg.setAttribute("role", "dialog");
    dlg.setAttribute("aria-modal", "true");
    dlg.setAttribute("aria-label", "在地圖上點選");
    dlg.innerHTML = `
        <div class="mapcard">
            <div class="maphead">
                <strong>在地圖上點選 (pick on the map)</strong>
                <span class="maphint">拖曳地圖或點一下，把準心對準要的位置</span>
            </div>
            <div class="mapview">
                <div class="maptiles"></div>
                <div class="mappin"></div>
                <div class="mapzoom">
                    <button type="button" class="zin" title="zoom in">+</button>
                    <button type="button" class="zout" title="zoom out">&minus;</button>
                </div>
                <div class="mapattr">&copy; <a href="https://www.openstreetmap.org/copyright"
                    target="_blank" rel="noopener">OpenStreetMap</a> contributors</div>
            </div>
            <div class="mapfoot">
                <span class="mapcoord"></span>
                <span class="mapz"></span>
                <span class="mapbtns">
                    <button type="button" class="cancel">取消</button>
                    <button type="button" class="ok">確定</button>
                </span>
            </div>
        </div>`;

    const view = dlg.querySelector(".mapview");
    const layer = dlg.querySelector(".maptiles");
    const zin = dlg.querySelector(".zin");
    const zout = dlg.querySelector(".zout");
    const coordEl = dlg.querySelector(".mapcoord");
    const zoomEl = dlg.querySelector(".mapz");

    /* Live <img> tiles, keyed z/x/y (with the unwrapped x, so the copies of the
     * world either side of the date line stay separate elements). Keeping them
     * between renders is what stops a pan from re-requesting the tile already
     * on screen. */
    const tiles = new Map();

    /* The coordinate under the crosshair, rounded the way currentPosition()
     * rounds: 6 decimals is ~0.1 m, far finer than the pixel it came from. */
    function reading() {
        return { lat: Number(center.lat.toFixed(6)), lon: Number(center.lon.toFixed(6)) };
    }

    /* Screen point (relative to the view) -> the coordinate under it. */
    function pointAt(px, py) {
        const x = mapWorldX(center.lon, z) - view.clientWidth / 2 + px;
        const y = mapWorldY(center.lat, z) - view.clientHeight / 2 + py;
        return { lat: mapLatAt(y, z), lon: mapWrapLon(mapLonAt(x, z)) };
    }

    function render() {
        const w = view.clientWidth;
        const h = view.clientHeight;
        const left = mapWorldX(center.lon, z) - w / 2;
        const top = mapWorldY(center.lat, z) - h / 2;
        const n = 2 ** z;   // tiles per side at this zoom

        const wanted = new Set();
        for (let ty = Math.floor(top / MAP_TILE_SIZE); ty <= Math.floor((top + h) / MAP_TILE_SIZE); ty++) {
            if (ty < 0 || ty >= n) continue;   // past a pole there is no tile row
            for (let tx = Math.floor(left / MAP_TILE_SIZE); tx <= Math.floor((left + w) / MAP_TILE_SIZE); tx++) {
                const key = `${z}/${tx}/${ty}`;
                wanted.add(key);
                let img = tiles.get(key);
                if (!img) {
                    img = new Image();
                    img.className = "maptile";
                    img.alt = "";
                    img.draggable = false;
                    img.src = MAP_TILE_URL
                        .replace("{z}", String(z))
                        .replace("{x}", String(((tx % n) + n) % n))   // wrap round the world
                        .replace("{y}", String(ty));
                    layer.appendChild(img);
                    tiles.set(key, img);
                }
                img.style.left = `${Math.round(tx * MAP_TILE_SIZE - left)}px`;
                img.style.top = `${Math.round(ty * MAP_TILE_SIZE - top)}px`;
            }
        }
        for (const [key, img] of tiles) {
            if (!wanted.has(key)) { img.remove(); tiles.delete(key); }
        }

        const { lat: rlat, lon: rlon } = reading();
        coordEl.textContent = `${rlat},${rlon}`;
        zoomEl.textContent = `zoom ${z}`;
        zin.disabled = z >= MAP_MAX_ZOOM;
        zout.disabled = z <= MAP_MIN_ZOOM;
    }

    /* Drag: the map moves with the finger, so the centre moves against it. The
     * y clamp is what stops a hard flick from throwing the view past a pole. */
    function panBy(dx, dy) {
        const size = MAP_TILE_SIZE * 2 ** z;
        const x = mapWorldX(center.lon, z) - dx;
        const y = mapClamp(mapWorldY(center.lat, z) - dy, 0, size);
        center = { lat: mapLatAt(y, z), lon: mapWrapLon(mapLonAt(x, z)) };
        render();
    }

    /* Zoom about a screen point: whatever is under (ax, ay) is still under it
     * afterwards, so the wheel zooms into the cursor and a pinch into the
     * fingers. The buttons pass the centre, which is the crosshair. */
    function zoomTo(next, ax, ay) {
        const target = mapClamp(next, MAP_MIN_ZOOM, MAP_MAX_ZOOM);
        if (target === z) return;
        const w = view.clientWidth;
        const h = view.clientHeight;
        const anchorX = ax === undefined ? w / 2 : ax;
        const anchorY = ay === undefined ? h / 2 : ay;
        const held = pointAt(anchorX, anchorY);
        z = target;
        const x = mapWorldX(held.lon, z) + (w / 2 - anchorX);
        const y = mapWorldY(held.lat, z) + (h / 2 - anchorY);
        center = { lat: mapLatAt(y, z), lon: mapWrapLon(mapLonAt(x, z)) };
        render();
    }

    return new Promise((resolve) => {
        function close(value) {
            window.removeEventListener("resize", render);
            document.removeEventListener("keydown", onKey);
            dlg.remove();
            resolve(value);
        }
        function onKey(event) {
            if (event.key === "Escape") { event.preventDefault(); close(null); }
        }

        /* Pointer events, so one set of handlers covers mouse, pen and touch.
         * Two fingers down means a pinch, and pinching is stepped rather than
         * smooth: fractional zoom would mean scaling the tile layer, and whole
         * levels are what the tile scheme actually has. */
        const pointers = new Map();
        let dragged = false;
        let pinchBase = 0;

        function pinchSpan() {
            const [a, b] = [...pointers.values()];
            return Math.hypot(a.x - b.x, a.y - b.y);
        }
        function pinchMid() {
            const [a, b] = [...pointers.values()];
            const box = view.getBoundingClientRect();
            return [(a.x + b.x) / 2 - box.left, (a.y + b.y) / 2 - box.top];
        }

        view.addEventListener("pointerdown", (event) => {
            // The zoom buttons and the attribution sit inside the map, so their
            // pointer events bubble to here. Left alone, pressing + is a
            // pointerdown and pointerup that never moved -- a tap -- and the tap
            // rule would drag the top-right corner to the crosshair before the
            // click zoomed, so + and - would walk the coordinate away instead of
            // holding it. Skipping the press here is enough: pointermove and the
            // release both no-op on a pointer id they never recorded.
            if (event.target.closest(".mapzoom, .mapattr")) return;
            // Capture so a drag that leaves the map still reaches these
            // handlers. Wrapped because a pointer id the browser no longer
            // considers active throws, and a drag is not worth an exception.
            try { view.setPointerCapture(event.pointerId); } catch (err) { /* fine */ }
            pointers.set(event.pointerId, {
                x: event.clientX, y: event.clientY,
                x0: event.clientX, y0: event.clientY,
            });
            dragged = false;
            pinchBase = pointers.size >= 2 ? pinchSpan() : 0;
            view.classList.add("dragging");
        });

        view.addEventListener("pointermove", (event) => {
            const was = pointers.get(event.pointerId);
            if (!was) return;
            const dx = event.clientX - was.x;
            const dy = event.clientY - was.y;
            pointers.set(event.pointerId, { ...was, x: event.clientX, y: event.clientY });
            if (Math.hypot(event.clientX - was.x0, event.clientY - was.y0) > MAP_DRAG_SLOP) {
                dragged = true;
            }
            if (pointers.size >= 2) {
                const span = pinchSpan();
                if (!pinchBase || !span) return;
                if (span / pinchBase > MAP_PINCH_STEP) {
                    zoomTo(z + 1, ...pinchMid());
                    pinchBase = span;
                } else if (pinchBase / span > MAP_PINCH_STEP) {
                    zoomTo(z - 1, ...pinchMid());
                    pinchBase = span;
                }
                return;   // two fingers zoom; they do not also pan
            }
            panBy(dx, dy);
        });

        function release(event) {
            if (!pointers.delete(event.pointerId)) return;
            if (pointers.size < 2) pinchBase = 0;
            if (pointers.size > 0) return;
            view.classList.remove("dragging");
            if (!dragged) {
                // A tap, not a drag: bring what was tapped to the crosshair,
                // where it is visible and can be nudged.
                const box = view.getBoundingClientRect();
                center = pointAt(event.clientX - box.left, event.clientY - box.top);
                render();
            }
        }
        view.addEventListener("pointerup", release);
        view.addEventListener("pointercancel", release);

        view.addEventListener("wheel", (event) => {
            event.preventDefault();   // the page behind must not scroll
            const box = view.getBoundingClientRect();
            zoomTo(z + (event.deltaY < 0 ? 1 : -1),
                   event.clientX - box.left, event.clientY - box.top);
        }, { passive: false });

        view.addEventListener("dblclick", (event) => {
            if (event.target.closest(".mapzoom, .mapattr")) return;   // as above
            const box = view.getBoundingClientRect();
            zoomTo(z + 1, event.clientX - box.left, event.clientY - box.top);
        });

        zin.addEventListener("click", () => zoomTo(z + 1));
        zout.addEventListener("click", () => zoomTo(z - 1));
        dlg.querySelector(".ok").addEventListener("click", () => close(reading()));
        dlg.querySelector(".cancel").addEventListener("click", () => close(null));
        // Only a click that both starts and ends on the backdrop dismisses, so
        // a pan that overshoots the map does not throw the dialog away.
        dlg.addEventListener("click", (event) => { if (event.target === dlg) close(null); });

        document.body.appendChild(dlg);
        window.addEventListener("resize", render);
        document.addEventListener("keydown", onKey);
        render();   // after the append: the tile grid is sized from the view
        dlg.querySelector(".ok").focus();
    });
}
