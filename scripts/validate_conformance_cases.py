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

    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors[:10]:
            print("  ", err)
        exit(1)
    else:
        print(f"SUCCESS: All {len(all_case_dirs)} conformance test cases passed validation against JSON schemas!")

if __name__ == "__main__":
    main()
