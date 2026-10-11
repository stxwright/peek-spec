# peek-spec

Normative protocol for Peek: recipe format, registry format, result document,
extraction semantics, and the conformance suite every client must pass.

## Layout

- `peek_spec.md` — system specification (draft). Start here.
- `schemas/` — JSON Schemas: `recipe`, `registry`, `index`, `result`.
- `conformance/` — executable conformance cases (`cases/`, `cases-optional/`)
  plus `README.md` describing the harness.
- `scripts/` — `validate_schemas.py`, `build_conformance_cases.py`,
  `validate_conformance_cases.py`.

## Relationship to other repos

| Repo | Role |
|---|---|
| `peek-registry` | The recipes; validated against `schemas/recipe.schema.json` |
| `peek-android` | Kotlin client; extraction behaviour must satisfy `conformance/` |
| `peek-cli` | Python workbench; same conformance gate |

Recipe authors and client implementers: the conformance cases are the
executable contract. If the prose and a case disagree, the case wins —
then fix the prose.
