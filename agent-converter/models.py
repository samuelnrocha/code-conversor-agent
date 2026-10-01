from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class FeasibilityStatus(Enum):
    FEASIBLE = "FEASIBLE"
    NOT_FEASIBLE = "NOT_FEASIBLE"

@dataclass
class SourceCodeFile:
    relative_path: str
    absolute_path: str
    content: str
    lines_of_code: int
    ast_hints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CompatibilityAnalysis:
    status: FeasibilityStatus
    score: float # 0.0 to 100.0
    detected_features: List[str]
    php_equivalents: Dict[str, str]
    blockers: List[str]
    warnings: List[str]
    recommendations: List[str]

@dataclass
class DependencyMapping:
    csharp_namespaces: List[str]
    target_php_namespaces: Dict[str, str]
    mapped_types: Dict[str, str]
    composer_packages: Dict[str, str]

@dataclass
class ReviewIssue:
    file_path: str
    severity: str # "INFO", "WARNING", "ERROR"
    message: str
    suggested_fix: Optional[str] = None

@dataclass
class ReviewReport:
    passed: bool
    total_files_reviewed: int
    issues: List[ReviewIssue]
    summary: str

@dataclass
class TestResult:
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration_ms: float
    output_log: str
    success: bool
