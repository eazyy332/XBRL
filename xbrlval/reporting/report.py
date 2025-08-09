from __future__ import annotations

from typing import List
from xbrlval.core.models import ValidationReport as VR, ValidationIssue


class ValidationReport(VR):
    @classmethod
    def from_issues(cls, issues: List[ValidationIssue]) -> "ValidationReport":
        return cls(issues=issues)