from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import boto3

from ..models.scheme import Scheme, schemes_from_payload


class RulesService:
    """
    Loads and exposes scheme rules, either from a local JSON file
    (rules_path) or from a DynamoDB table (dynamodb_table).

    Exactly one of rules_path / dynamodb_table should be provided.
    """

    def __init__(
        self,
        rules_path: Optional[Path] = None,
        dynamodb_table: Optional[str] = None,
        aws_region: str = "ap-south-1",
    ):
        self._rules_path = Path(rules_path) if rules_path else None
        self._dynamodb_table = dynamodb_table
        self._aws_region = aws_region
        self._schemes: List[Scheme] = []
        self.reload()

    def reload(self) -> None:
        if self._dynamodb_table:
            payload = self._load_from_dynamodb()
        else:
            with self._rules_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        self._schemes = schemes_from_payload(payload)

    def _load_from_dynamodb(self) -> dict:
        """
        Scans the configured DynamoDB table and wraps the results in the
        same {"schemes": [...]} shape schemes_from_payload() already expects,
        so no changes are needed to the parsing logic in models/scheme.py.
        """
        dynamodb = boto3.resource("dynamodb", region_name=self._aws_region)
        table = dynamodb.Table(self._dynamodb_table)

        items = []
        response = table.scan()
        items.extend(response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        return {"schemes": items}

    @property
    def schemes(self) -> List[Scheme]:
        return self._schemes

    def as_dict(self) -> list[dict]:
        return [s.to_dict() for s in self._schemes]