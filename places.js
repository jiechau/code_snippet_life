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
