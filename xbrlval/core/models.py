from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "error"  # error, warning, info
    location: Optional[str] = None  # e.g., element QName or file:line
    rule: Optional[str] = None


class ValidationReport(BaseModel):
    issues: List[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issues": [i.model_dump() for i in self.issues],
            "errorCount": sum(1 for i in self.issues if i.severity == "error"),
            "warningCount": sum(1 for i in self.issues if i.severity == "warning"),
            "infoCount": sum(1 for i in self.issues if i.severity == "info"),
        }

    def to_sarif(self) -> Dict[str, Any]:
        return {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "xbrlval",
                            "informationUri": "https://example.com/xbrlval",
                            "rules": [],
                        }
                    },
                    "results": [
                        {
                            "ruleId": i.code,
                            "level": {
                                "error": "error",
                                "warning": "warning",
                                "info": "note",
                            }.get(i.severity, "error"),
                            "message": {"text": i.message},
                            "locations": (
                                [{"physicalLocation": {"artifactLocation": {"uri": i.location}}}]
                                if i.location
                                else []
                            ),
                        }
                        for i in self.issues
                    ],
                }
            ],
        }


@dataclass
class Entity:
    scheme: str
    identifier: str


@dataclass
class Period:
    type: str  # instant or duration
    start_date: Optional[str]
    end_date: Optional[str]
    instant: Optional[str]


@dataclass
class Context:
    id: str
    entity: Entity
    period: Period
    dimensions: Dict[str, str]


@dataclass
class Unit:
    id: str
    measures: List[str]
    numerator_measures: Optional[List[str]] = None
    denominator_measures: Optional[List[str]] = None


@dataclass
class Fact:
    concept: str
    value: Optional[str]
    context_ref: Optional[str]
    unit_ref: Optional[str]
    decimals: Optional[str]
    is_numeric: bool


@dataclass
class Instance:
    base_uri: str
    contexts: Dict[str, Context]
    units: Dict[str, Unit]
    facts: List[Fact]
    schema_locations: List[str]
    linkbase_locations: List[str]