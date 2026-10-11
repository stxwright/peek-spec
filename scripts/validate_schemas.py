import json
import yaml
import jsonschema
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    schemas_dir = root / "schemas"
    
    # Load all schemas
    schemas = {}
    for p in schemas_dir.glob("*.schema.json"):
        with open(p, "r", encoding="utf-8") as f:
            schemas[p.name] = json.load(f)
            jsonschema.Draft202012Validator.check_schema(schemas[p.name])
            print(f"OK: {p.name} is a valid Draft 2020-12 JSON Schema")
            
    # Validate §2.11 example recipe
    example_recipe_yaml = """
spec: 1
id: uk.co.example-rail.departures
version: 3
name: Station departures
description: Next departures between two stations.
params:
  - { key: from, label: From station code, type: string, pattern: "^[A-Z]{3}$", placeholder: EUS }
  - { key: to,   label: To station code,   type: string, pattern: "^[A-Z]{3}$", placeholder: MAN }
fetch:
  url: "https://www.example-rail.co.uk/live/{params.from}/{params.to}"
  format: html
  allowed_domains: ["www.example-rail.co.uk"]
  min_interval_s: 300
extract:
  fields:
    updated:
      from: [ { css: "p.last-updated" } ]
      transforms: [ { op: regex_extract, pattern: "(\\\\d{2}:\\\\d{2})" } ]
      type: time
      optional: true
  lists:
    departures:
      items: [ { css: "table.departures tbody tr" } ]
      min_items: 1
      limit: 10
      fields:
        time:
          from: [ { css: "td.time" }, { css: "[data-col=time]" } ]
          type: time
        dest:
          from: [ { css: "td.dest" } ]
        platform:
          from: [ { css: "td.platform" } ]
          optional: true
        status_text:
          from: [ { css: "td.status" } ]
          transforms: [ { op: collapse_ws } ]
        status:
          from: [ { css: "td.status" } ]
          type: severity
          transforms:
            - { op: map, table: { "On time": ok, "Delayed": warn, "Cancelled": bad }, else: neutral }
display:
  title: "{params.from} → {params.to}"
  layout: list
  source: departures
  limit: 5
  row:
    primary: "{time}  {dest}"
    secondary: "Platform {platform}"
    badge: { text: "{status_text}", severity: "{status}" }
  footer: "Updated {updated}"
  link: "https://www.example-rail.co.uk/live/{params.from}/{params.to}"
tests:
  fixtures:
    - name: normal
      file: fixtures/normal.html
      params: { from: EUS, to: MAN }
      now: "2026-09-30T08:00:00+01:00"
      expected: fixtures/normal.expected.json
  live:
    params: { from: EUS, to: MAN }
    assert:
      - { path: "lists.departures", op: count_gte, value: 1 }
"""
    recipe_data = yaml.safe_load(example_recipe_yaml)
    jsonschema.validate(recipe_data, schemas["recipe.schema.json"])
    print("OK: §2.11 example recipe validates against recipe.schema.json")

    # Validate §6.4 registry.json example
    registry_example = {
      "format": 1,
      "id": "peek-official",
      "name": "Peek Community Registry",
      "base_url": "https://example.github.io/peek-registry/",
      "repo": "https://github.com/example/peek-registry",
      "submit": { "repo": "example/peek-registry", "issue_form_url": "https://github.com/example/peek-registry/issues/new?template=submit-recipe.yml" },
      "report_broken_url_template": "https://github.com/example/peek-registry/issues/new?template=report-broken.yml&recipe={id}&version={version}&error={error_code}&client={client}",
      "signing_keys": [ { "key_id": "k1", "algorithm": "ed25519", "public_key": "abc123base64", "not_after": "2028-01-01" } ],
      "policy": {
        "min_interval_s": 300,
        "health": { "broken_after_consecutive_failures": 2, "unlist_after_days_broken": 14, "archive_after_days_broken": 90 },
        "canary": { "cron": "17 4 * * *", "per_host_spacing_s": 5 }
      },
      "blocked_domains": [ { "domain": "example.org", "reason": "owner request", "date": "2026-09-01" } ],
      "contact": "registry@example.org"
    }
    jsonschema.validate(registry_example, schemas["registry.schema.json"])
    print("OK: §6.4 registry.json example validates against registry.schema.json")

    # Validate §6.4 index.json example
    index_example = {
      "format": 1,
      "registry_id": "peek-official",
      "generated_at": "2026-10-01T04:30:00Z",
      "sequence": 1790829000,
      "min_client_spec": 1,
      "recipes": [
        {
          "id": "uk.co.example-rail.departures",
          "version": 3,
          "name": "Station departures",
          "description": "Next departures between two stations.",
          "params": [ { "key": "from", "label": "From station code", "type": "string", "required": True } ],
          "updated_at": "2026-09-28T10:00:00Z",
          "health": { "state": "healthy", "checked_at": "2026-10-01T04:20:00Z", "since": "2026-08-01T04:20:00Z" },
          "listed": True,
          "bundle": { "path": "r/uk.co.example-rail.departures/3.json", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "size": 4821 }
        }
      ],
      "revoked": [ { "id": "uk.co.bad.recipe", "versions": "*", "severity": "disable", "reason": "Security issue" } ]
    }
    jsonschema.validate(index_example, schemas["index.schema.json"])
    print("OK: §6.4 index.json example validates against index.schema.json")

    # Validate §3 result.json example
    result_example = {
      "spec": 1,
      "recipe": { "id": "uk.co.example-rail.departures", "version": 3 },
      "status": "ok",
      "data": {
        "fields": { "updated": "08:01" },
        "lists": {
          "departures": [
            { "time": "08:15", "dest": "Manchester Piccadilly", "platform": "5", "status_text": "On time", "status": "ok" }
          ]
        }
      },
      "view": {
        "title": "EUS → MAN",
        "layout": "list",
        "rows": [
          { "primary": "08:15  Manchester Piccadilly", "secondary": "Platform 5",
            "trailing": None, "badge": { "text": "On time", "severity": "ok" } }
        ],
        "items": None,
        "empty_text": None,
        "footer": "Updated 08:01",
        "link": "https://www.example-rail.co.uk/live/EUS/MAN"
      },
      "diagnostics": {
        "fallbacks_used": [ { "path": "lists.departures[2].time", "locator_index": 1 } ],
        "skipped_items": [ { "list": "departures", "index": 3, "reason": "FIELD_MISSING:time" } ],
        "warnings": []
      },
      "error": None
    }
    jsonschema.validate(result_example, schemas["result.schema.json"])
    print("OK: §3 result.json example validates against result.schema.json")

if __name__ == "__main__":
    main()
