# Peek Conformance Test Suite (v1)

This directory contains the normative conformance test cases for implementations of the **Peek Protocol** (v1).

## Conformance Standard

An implementation may claim **"Peek Spec 1.x Conformant"** if and only if:
1. It passes **100% of all required test cases** in `cases/`.
2. It explicitly declares which optional features (`cases-optional/`) it supports (e.g. `render.js`, `xpath`, `css.has`) and passes 100% of the cases for each declared feature.
3. It produces byte-identical or semantically equivalent canonical JSON according to [RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785) matching `expected.json`.

## Case Directory Layout

Each test case directory contains:

| File | Format | Description |
|---|---|---|
| `recipe.yaml` | YAML 1.2 / JSON | The recipe under test. |
| `params.json` | JSON object | The user-supplied parameters to pass into `plan_request` and `extract`. |
| `response.body` | Raw bytes | The HTTP response body (or serialized DOM snapshot for `render: js`). |
| `response.meta.json` | JSON object | Metadata: `{ status, final_url, headers }`. |
| `response.captured/` | Directory | (Optional) Contains captured response payloads for `render: js` tests. |
| `now.txt` | ISO 8601 string | The reference time with offset passed to `extract`. |
| `expected.json` | Canonical JSON | The expected canonical `Result` document (§3). |

## Runner Protocol

A conformance runner executes against a case directory by invoking:
```bash
peek-runner <path-to-case-directory>
```
The runner must:
1. Load `recipe.yaml`, `params.json`, `response.body`, `response.meta.json`, and `now.txt`.
2. Execute `extract(recipe, params, response, now)`.
3. Canonicalize the resulting `Result` document per RFC 8785.
4. Compare against `expected.json`.

## Test Suite Coverage

The suite contains **67 total cases** (62 required + 5 optional):

1. **CSS Selectors (`001`–`008`):** IDs, classes, attribute operators (`=`, `^=`, `$*`, `|=`, `~=`, `i` case-insensitivity), `:is()`, `:not()`, `:scope` within lists, nested child/descendant/sibling combinators.
2. **Locators (`009`–`016`):** `attr`, `text: "own"`, `text: "all"`, `nth`, `join`, `const`, JSONPath responses (`format: json`), and embedded JSON `<script>` tags with `json_path`.
3. **Fallbacks & Lists (`017`–`024`):** Locator fallback order, `fallbacks_used` diagnostics, `optional: true` returning `null`, `default` fallbacks, skipped invalid items with `skipped_items` diagnostics, `min_items` checks, `min_items: 0`, and list item truncation with `limit`.
4. **Transforms (`025`–`040`):** `trim`, `collapse_ws`, `upper`, `lower`, `replace`, `regex_replace` (with `$1`), `regex_extract`, `split` (positive & negative indices), `strip_prefix`, `strip_suffix`, `prepend`, `append`, `truncate` (Unicode-safe), `parse_number` (standard & European format), `parse_time`, `parse_datetime`, `map` (table match & `else`).
5. **Types (`041`–`048`):** `string`, `number`, `integer`, `boolean`, `time` (HH:MM normalization), `datetime` (ISO 8601 with offset), `severity`, `url` (relative URL resolution).
6. **Templates & Display (`049`–`054`):** Parameter and field interpolation, escaping `{{` and `}}`, the display **Null rule** (omitting the template if a reference is null), list and kv layouts, severity badges.
7. **Errors & Security (`055`–`062`):** `FIELD_MISSING`, `TOO_FEW_ITEMS`, `PARAM_INVALID`, `DOMAIN_NOT_ALLOWED`, `REDIRECT_NOT_ALLOWED`, `HTTP_STATUS`, `RESPONSE_TOO_LARGE`, `PARSE_ERROR`.
8. **Optional Features (`cases-optional/`):**
   - `render.js/001-rendered-dom-snapshot`: Client-rendered DOM simulation.
   - `render.js/002-captured-document`: Reading from `response.captured/` via `source: <name>`.
   - `render.js/003-captured-fallback`: Absent capture document falling back to page locator.
   - `xpath/001-xpath-basic`: XPath selection.
   - `css.has/001-css-has`: `:has()` selector.
