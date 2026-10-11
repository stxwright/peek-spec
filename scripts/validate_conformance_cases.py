import json
import yaml
import jsonschema
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    schemas_dir = root / "schemas"
    cases_dir = root / "conformance" / "cases"
    opt_dir = root / "conformance" / "cases-optional"

    with open(schemas_dir / "recipe.schema.json", "r", encoding="utf-8") as f:
        recipe_schema = json.load(f)
    with open(schemas_dir / "result.schema.json", "r", encoding="utf-8") as f:
        result_schema = json.load(f)

    all_case_dirs = list(cases_dir.glob("*")) + list(opt_dir.glob("*/*"))
    print(f"Validating {len(all_case_dirs)} conformance cases against JSON schemas...")

    errors = []
    for d in all_case_dirs:
        # Check files
        for fname in ["recipe.yaml", "params.json", "response.body", "response.meta.json", "now.txt", "expected.json"]:
            if not (d / fname).exists():
                errors.append(f"{d.name}: missing {fname}")

        # Validate recipe.yaml against recipe.schema.json
        try:
            with open(d / "recipe.yaml", "r", encoding="utf-8") as f:
                r_data = yaml.safe_load(f)
            jsonschema.validate(r_data, recipe_schema)
        except Exception as e:
            errors.append(f"{d.name} recipe.yaml validation error: {e}")

        # Validate params.json
        try:
            with open(d / "params.json", "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            errors.append(f"{d.name} params.json error: {e}")

        # Validate expected.json against result.schema.json
        try:
            with open(d / "expected.json", "r", encoding="utf-8") as f:
                exp_data = json.load(f)
            jsonschema.validate(exp_data, result_schema)
        except Exception as e:
            errors.append(f"{d.name} expected.json validation error: {e}")

    # v2 series (implemented profile): structural check only — behavioural
    # pinning is executed by clients (peek-cli tests/test_conformance.py).
    v2_dir = root / "conformance" / "cases-v2"
    v2_cases = sorted(p for p in v2_dir.iterdir() if p.is_dir()) if v2_dir.is_dir() else []
    for d in v2_cases:
        for fname in ["recipe.yaml", "response.body", "expected.json"]:
            if not (d / fname).exists():
                errors.append(f"cases-v2/{d.name}: missing {fname}")
        try:
            with open(d / "recipe.yaml", "r", encoding="utf-8") as f:
                r_data = yaml.safe_load(f)
            if not isinstance(r_data, dict) or r_data.get("format") != 2:
                errors.append(f"cases-v2/{d.name}: recipe.yaml must be a format: 2 mapping")
        except Exception as e:
            errors.append(f"cases-v2/{d.name} recipe.yaml error: {e}")
        try:
            with open(d / "expected.json", "r", encoding="utf-8") as f:
                exp_data = json.load(f)
            ex = exp_data.get("extract")
            if not isinstance(ex, dict) or not isinstance(ex.get("rows"), list) or \
                    ("error" not in ex and "error_prefix" not in ex):
                errors.append(f"cases-v2/{d.name}: expected.json needs "
                              f"extract{{rows, error|error_prefix}}")
            if "table" not in exp_data:
                errors.append(f"cases-v2/{d.name}: expected.json needs table key")
        except Exception as e:
            errors.append(f"cases-v2/{d.name} expected.json error: {e}")
    print(f"Checked {len(v2_cases)} cases-v2 fixtures structurally.")

    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors[:10]:
            print("  ", err)
        exit(1)
    else:
        print(f"SUCCESS: All {len(all_case_dirs)} conformance test cases passed validation against JSON schemas!")

if __name__ == "__main__":
    main()
