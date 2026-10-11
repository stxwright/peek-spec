# peek-spec

Normative protocol for Peek: recipe format, registry format, result document,
extraction semantics, and the conformance suite every client must pass.

## Layout

- `peek_spec.md` — system specification (draft, aspirational v1 track). Start here.
- `docs/extraction-v2.md` — **normative** extraction semantics for the
  implemented `format: 2` profile. This is what ships; read this first.
- `schemas/` — JSON Schemas: `recipe`, `registry`, `index`, `result`
  (v1 track; the registry does not currently validate against these).
- `conformance/` — `cases/` (v1 aspirational suite) and `cases-v2/`
  (implemented profile; **required** for a v2 conformance claim) plus
  per-directory READMEs describing each harness.
- `scripts/` — `validate_schemas.py`, `build_conformance_cases.py`,
  `validate_conformance_cases.py`.

## Relationship to other repos

| Repo | Role |
|---|---|
| `peek-registry` | The recipes; validated by `peek-registry/scripts/validate_v2.py` against the `format: 2` profile (`docs/extraction-v2.md`, `conformance/cases-v2/`) |
| `peek-android` | Kotlin client; extraction behaviour must satisfy `conformance/` |
| `peek-cli` | Python workbench; same conformance gate |

Recipe authors and client implementers: the conformance cases are the
executable contract. If the prose and a case disagree, the case wins —
then fix the prose.
