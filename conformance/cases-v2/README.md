# v2 conformance series

Behavioural pinning for the **implemented** `format: 2` profile
(see `docs/extraction-v2.md`). Any client claiming v2 conformance MUST pass
every case in this directory. The v1 suite in `../cases/` is the aspirational
track and is NOT required for a v2 claim.

## Case layout

Each case is a directory with:

- `recipe.yaml` — a `format: 2` recipe (valid per the registry validator).
- `response.body` — the document to extract from.
- `expected.json` — the expected result (shape below).

## Runner protocol (`peek-runner <case-dir>`)

1. Parse `recipe.yaml`. Params resolve from recipe defaults (no override file
   in v1 of this series; recipes SHOULD use defaults that exercise the case).
2. Load `response.body` into a **rendered DOM in Chromium**. Fixtures MUST use
   only visible, script-free, self-contained markup so `innerText` agrees with
   `textContent` in any conformant runner (see constraints).
3. Run the extraction algorithm from `docs/extraction-v2.md` §4 against the
   live DOM (same selector engine, same `clean()`, same key/limit rules).
4. Run the table build from §6.
5. Compare parsed-JSON deep equality against `expected.json`.

`expected.json` shape:

```json
{
  "extract": {
    "rows": [ { "field": "value|null", "...": "..." } ],
    "error": null
  },
  "table": {
    "title": "...",
    "headers": ["A", "B"] ,
    "rows": [["a", "b"]]
  }
}
```

- `table` is `null` when no table is produced (§6).
- `error` compares by exact string match, EXCEPT a case may give
  `"error_prefix"` instead of `"error"`, which passes when the actual error
  starts with that prefix (used where engine error text varies, e.g. invalid
  selector messages).
- `rows` field values are strings or `null`, in document order.

## Fixture constraints (load-bearing)

- Visible elements only. NOTHING may depend on hidden elements,
  `display:none`, or layout-dependent `innerText` differences.
- No `<script>`, no external resources, no network. The body is the whole
  world.
- Keep bodies minimal: every element must earn its place in the expectation.

## Case inventory

| Case | Covers (`extraction-v2.md` §) |
|---|---|
| `001-rows-basic` | §4 row loop, multi-row table (§6) |
| `002-key-drop` | §4.3 falsy key drops row |
| `003-limit` | §4.3 limit clamp |
| `004-single-item-transpose` | §4.4/§6 label-value transpose, empty pair drop |
| `005-page-scope-title` | §4.2 page fields merged; title from row zero (§5) |
| `006-no-rows-error` | §4.5 `no rows matched` |
| `007-bad-selector-error` | §4.5 `rows selector failed` (prefix rule) |
| `008-attr-read` | §4.1 verbatim `getAttribute` |
| `009-scope-self` | §4.2 `sel: ":scope"` |
| `010-title-strip` | §5 unresolvable refs stripped, ws collapsed |
| `011-row-groups` | §4.6 groups: const merge, key-drop, cross-group limit |

Note: fixtures test engine behaviour, which is wider than what the registry
validator permits authors to write. `010-title-strip` is intentionally
registry-invalid (`title: {missing} is not a param or field`) — the engine
must still degrade gracefully if such a recipe is loaded locally.
