"""
Loads rules/schemes.v1.json into the DynamoDB 'Schemes' table.

Usage:
    Run this from the root of your OpenBenefits repo (so the relative
    path to rules/schemes.v1.json resolves correctly), after running
    `aws configure` with your sravan-admin access key.

    python migrate_schemes_to_dynamodb.py
"""

import json
import boto3
from pathlib import Path

REGION = "ap-south-1"
TABLE_NAME = "Schemes"
SCHEMES_FILE = Path("rules/schemes.v1.json")


def main():
    if not SCHEMES_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {SCHEMES_FILE}. Run this script from the "
            "root of your OpenBenefits repo."
        )

    with open(SCHEMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The file has metadata + a list of schemes — adjust key name below
    # if your actual JSON structure differs (e.g. data["schemes"]).
    schemes = data.get("schemes", data) if isinstance(data, dict) else data

    if not isinstance(schemes, list):
        raise ValueError(
            "Expected a list of scheme objects. Check schemes.v1.json "
            "structure and adjust the 'schemes = ...' line above."
        )

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)

    loaded = 0
    with table.batch_writer() as batch:
        for scheme in schemes:
            if "id" not in scheme:
                print(f"Skipping scheme with no 'id': {scheme.get('name', '???')}")
                continue
            batch.put_item(Item=scheme)
            loaded += 1

    print(f"Done. Loaded {loaded} schemes into '{TABLE_NAME}' ({REGION}).")


if __name__ == "__main__":
    main()
