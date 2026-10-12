# Peek v2 — extraction semantics (implemented profile)

Status: **normative for what ships**. This documents the `format: 2` recipe
profile as implemented by `peek-android` (`RecipeEngine`) and validated by
`peek-registry` (`validate_v2.py`). It is extracted from the implementation,
not the other way round: where this doc and the code disagree, the code wins —
then fix this doc.

The v1 protocol in `peek_spec.md` (`spec: 1`, `extract:`/`display:`/`tests:`,
transforms, error codes) is the **aspirational track**: nothing implements it
yet. The v1 conformance suite in `conformance/cases/` is gated on that track.
Clients MUST pass the **v2 series** in `conformance/cases-v2/` instead.

## 1. Recipe document

One YAML (or JSON) document per recipe. Unknown top-level keys are rejected
by the registry validator. All keys are strings.

| Key | Required | Type / constraint | Default | Notes |
|---|---|---|---|---|
| `format` | yes | int, MUST be `2` | — | Anything else is rejected/skipped by sync |
| `id` | yes | reverse-domain, `==` folder name | — | Immutable |
| `version` | yes | int `>= 1` | — | `+1` per publish; displayed, bound per widget |
| `name` | yes | 1–60 chars | — | Header fallback when title resolves empty |
| `description` | yes | 1–280 chars | — | Browse card |
| `params` | no | map string→string or descriptor (§2.1) | `{}` | Plain defaults; descriptors add guidance |
| `fetch` | yes | object (§2) | — | |
| `rows` | no | CSS selector (§4) or list of `{sel, values}` groups (§4.6), `<= 500` chars per selector | absent | Absent = single-item (document) recipe |
| `fields` | yes | non-empty map (§3) | — | |
| `key` | iff `rows` present | names a row-scoped field | — | Rows with empty `key` value are dropped |
| `limit` | no | int 1–100 | `10` | Rows only |
| `title` | no | template (§5) | `""` | |
| `columns` | yes | 1–10 field names | — | Display order; MUST name row-scoped fields |
| `link` | no | https URL, template (§5) | — | Host MUST be in `fetch.allow`; refs MUST be params |

## 2. Params and URL substitution

- Substitution is literal string replacement, applied in this order per key:
  `{params.<k>}` then `{<k>}`. No URL-encoding. Unfilled placeholders are left
  as-is in the URL.
- Params override fields in title interpolation (§5).
- `fetch.url` MUST start with `https://`; the scheme+host MUST be literal
  (no `{..}` in the host) and the host MUST be listed in `fetch.allow`.

### 2.1 Param descriptors (guided input)

A param value is either a plain string (the default, as today) or a descriptor:

```yaml
params:
  stop: 690313                         # plain: default only
  competition:                         # descriptor
    default: english-premiership
    options:                           # optional closed set -> selection UI
      - value: english-premiership
        label: English Premiership
    help: "..."                        # optional hint/lookup instructions
```

- `default` (required in descriptors): the effective value until overridden.
- `options`: 1+ `{value, label}` entries, values unique, `default` MUST be
  one of them. Clients SHOULD offer the labels as a selection list.
- `help`: free text shown as input hint (e.g. where to find a stop code).
- Unknown descriptor keys are rejected. Runtime overrides (`--param k=v`,
  stored widget values) replace the effective value wholesale and are NOT
  checked against `options` — authors need freedom to probe unverified values.
- Resolution everywhere (URL, title, link): descriptors behave exactly as
  their `default` until overridden.

## 3. Fetch

| Key | Required | Constraint | Default |
|---|---|---|---|
| `url` | yes | https, literal host ∈ `allow` | — |
| `allow` | yes | `>= 1` literal hostnames | — |
| `every` | no | `>= 900` | `900` |
| `wait` | no | CSS selector, `<= 500` chars | — |

Client behaviour (as implemented):

- The widget update path **always renders** via WebView. There is no static
  fetch strategy; static HTTP fetch exists only in diagnostics.
- `wait`, when present, is an **existence check**: ready when
  `document.querySelector(wait)` exists. Invalid selector ⇒ never ready ⇒
  collection falls through to timeout.
- Without `wait`, ready = body text matches a time pattern (or needle, in
  diagnostics). Poll every 100 ms; collect 250 ms after ready; collect anyway
  after 15 s; hard net of +20 s if `onPageFinished` never fires.
- Wait failure produces **no error of its own**; the extractor then typically
  returns `no rows matched` (§4.5).

## 4. Extraction

The extractor runs in-page as a single IIFE. Equivalent pseudo-code:

```
items = rowsSel ? document.querySelectorAll(rowsSel)   // may throw
        : [document]
```
For the list form, items are the per-group matches concatenated in listed
order (see §4.6); the loop below is unchanged and `limit` counts kept rows
across all groups.
```
pageVals = { k: readField(document, fdef)
             for k, fdef in fields if fdef.scope == 'page' }
rows = []
for item in items (up to limit):
    row = { k: pageVals[k] if page-scoped else readField(item, fdef) }
    if key and not row[key]: continue                  // falsy drops
    rows.push(row)
```

### 4.1 Field reading

```
readField(rootEl, fdef):
    sel  = fdef if string else fdef.sel or ''
    attr = fdef.attr if object else null
    if not sel: return null
    nodes = [rootEl] if sel == ':scope' else rootEl.querySelectorAll(sel)
    parts = [ clean(raw) for node in nodes
              raw = node.getAttribute(attr) if attr
                    else (node.innerText or node.textContent or '')
              if raw is not null and clean(raw) != '' ]
    return ' '.join(parts) if parts else null
```

- `clean(s)` is exactly `String(s).replace(/\s+/g, ' ').trim()`.
- Default text is `innerText || textContent`. There is **no visibility
  filtering**: hidden elements are read like any other, and in hidden/limited
  layout contexts `innerText` may be empty where `textContent` is not (known
  failure mode, unmitigated).
- `attr` is passed verbatim to `getAttribute`. There are no `text`/`inner`/
  `outer`/`href`/`value` keywords; `attr: "href"` works because it names a
  real attribute. No `innerHTML`/`outerHTML` access.
- All matches join with a single space. Empty/missing ⇒ `null` (never `""`).
  A failed field read never errors the row.

### 4.2 Scoping

- Row fields evaluate `querySelectorAll` **scoped to the row element**.
- `{scope: page}` fields evaluate once against `document` and are merged into
  **every** row (so title templates resolve from row zero). String-shorthand
  fields can never be page-scoped. `columns` MUST NOT name page-scoped fields.
- `sel: ":scope"` addresses the row element itself. No iframe/shadow-DOM
  piercing; no selector splitting or rewriting.

### 4.3 Key and limit

- Falsy `limit` (`0`/missing) ⇒ `10` (validator range is 1–100; the engine
  applies `limit || 10`).
- If `key` is set and `row[key]` is falsy (`null`/`""`/`0`/`false`/missing),
  the row is dropped — the `.filter(r => r.time)` equivalent.

### 4.4 Single-item recipes

`rows` absent/empty ⇒ one item (`document`); the table transposes to
label/value pairs (§6). `key`, if present, MUST name a field.

### 4.5 Output and errors

Output is always `{rows: [...], error: string|null}`. `rows` is an array of
`{field: string|null}` objects (page fields duplicated per row). `error` is
produced in exactly two cases:

1. `rows selector failed: <message>` — `querySelectorAll(rows)` threw.
2. `no rows matched: <rowsSel>` — only when a `rows` selector was given AND
   zero rows survived.

A recipe-specific empty/board notice (`empty:`) is **not part of v2**; rows
empty with no error is simply empty data.

### 4.6 Row groups

`rows` may instead be a non-empty list of groups, each
`{sel: "<css>", values: {name: "literal", ...}}`. Groups evaluate in listed
order; each group's matches are extracted exactly like §4 rows, then the
group's `values` fill any field the extraction left empty (literals only —
no `{ref}` interpolation; extraction wins ties). Use this when the section
label lives in an ancestor the row cannot see (one recipe over several
labeled blocks). `columns` and `title` may name group-value keys (title
still resolves from row zero); `key` MUST name an extracted row field.
A group `sel` that throws produces `rows selector failed: <message>` naming
that selector; zero rows overall reports `no rows matched` with the group
sels joined by ` + `.

## 5. Title and link templates

`interpolate(template, params, fields)`:

1. Per param: replace `{params.k}` then `{k}`. Params win over fields.
2. Per field: replace `{k}` with the field value (`null` ⇒ `""`).
3. Strip any remaining `{token}` (`[a-zA-Z0-9_.]+`); collapse whitespace; trim.

Consequences: unresolvable refs vanish silently (no error); title resolves
from **row zero only**; an empty title falls back to the recipe `name` at
render time. `title` refs MUST be params, fields, or group-value keys;
`link` refs MUST be params (validator-enforced).

## 6. Table building

- `columns` absent/empty ⇒ no table. Column order = display order; headers
  are `FIELD_NAME.replace('_',' ').upper()`.
- Multi-row: cell = `interpolate("{<col>}", params, row)`; rows where **all**
  cells are empty are dropped; all dropped ⇒ no table. Clamped to `limit`.
- Single-item: one `[LABEL, value]` pair per column; pairs with empty value
  dropped; all dropped ⇒ no table. Headers are `null` (label column styling).
- Text fallback truncates cells to 20 chars (`…`).

## 7. Explicitly NOT in v2

JS hooks; JSONPath/XPath/`const` locators; `nth`/`join`/`text: own`; fallback
locator chains; transforms; typed fields; per-field defaults; `fetch.method`/
headers/body; format declarations; captures; display layouts/badges/footers/
`empty_text`; fixtures/goldens/live assertions; error codes/diagnostics;
feature flags; signing. Proposals in these areas belong to the v1 track.

## 8. Conformance

Behavioural pinning lives in `conformance/cases-v2/` (runner protocol in that
directory's README). Any client claiming v2 conformance MUST pass every case.
If the prose above and a case disagree, the case wins — then fix the prose.
