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
    ["三總", 25.070602, 121.592399],
    ["瑞光路", 25.0781166, 121.5703769],
    ["大崙頭山", 25.108896, 121.585339],
    ["大武崙砲台", 25.157534, 121.709982],
    ["烏石港", 24.870683, 121.839613],
    ["東澳", 24.508322, 121.838141],
    ["石梯坪", 23.4913949, 121.4882516],
    ["柚子湖", 22.6657971, 121.5086903],
    ["龍磐公園", 21.922833, 120.8274758],
    ["暗空公園", 24.1182852, 121.2350106],
];

/* The page's starting coordinates, taken from the first spot above. */
const [, DEFAULT_LAT, DEFAULT_LON] = PLACES[0];
