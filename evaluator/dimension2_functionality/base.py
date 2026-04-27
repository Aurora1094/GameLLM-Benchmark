from dataclasses import dataclass, field
from typing import Any


@dataclass
class FunctionalityResult:
    passed: int
    total: int
    criteria_scores: dict[str, int] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "total": self.total,
            "score": self.score,
            "criteria_scores": self.criteria_scores,
            "reasons": self.reasons,
            "evidence": self.evidence,
        }
