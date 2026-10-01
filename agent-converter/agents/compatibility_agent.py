import os
import re
from pathlib import Path
from typing import List, Dict
from models import CompatibilityAnalysis, FeasibilityStatus, SourceCodeFile

class CompatibilityAnalysisAgent:
    """
    Agente de análise de compatibilidade de recursos .NET/C# 
    com bibliotecas e recursos do PHP até o 8.4.
    """

    KNOWN_BLOCKERS = [
        ("System.Runtime.InteropServices", "P/Invoke / Unmanaged C/C++ memory binding - requires PHP FFI or native extension"),
        ("System.Windows.Forms", "Desktop UI (WinForms) has no direct PHP CLI/Web equivalent"),
        ("System.Windows.Controls", "WPF GUI has no direct PHP CLI/Web equivalent"),
        ("System.EnterpriseServices", "COM+ / Enterprise Services deprecated Windows-only infrastructure")
    ]

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)

    def scan_files(self) -> List[SourceCodeFile]:
        code_files = []
        for path in self.source_dir.rglob("*.cs"):
            if "bin" in path.parts or "obj" in path.parts:
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                code_files.append(SourceCodeFile(
                    relative_path=str(path.relative_to(self.source_dir)),
                    absolute_path=str(path),
                    content=content,
                    lines_of_code=len(content.splitlines())
                ))
        return code_files

    def analyze(self) -> CompatibilityAnalysis:
        files = self.scan_files()
        all_code = "\n".join(f.content for f in files)

        detected_features = []
        php_equivalents = {}
        blockers = []
        warnings = []
        recommendations = []

        # Check for blockers
        for token, reason in self.KNOWN_BLOCKERS:
            if token in all_code:
                blockers.append(f"Incompatible dependency: {token} ({reason})")

        # Feature Detection & PHP 8.4 Mapping
        if "record " in all_code or "sealed record" in all_code:
            detected_features.append("C# Records (Immutable DTOs / Value Objects)")
            php_equivalents["C# Records"] = "PHP 8.2+ readonly class with promoted constructor properties"

        if "enum " in all_code:
            detected_features.append("C# Enums (Type-safe Enumerations)")
            php_equivalents["C# Enums"] = "PHP 8.1+ Backed Enums with int/string values and custom methods"

        if "decimal" in all_code:
            detected_features.append("C# decimal (High-precision monetary values)")
            php_equivalents["C# decimal"] = "PHP bcmath or precision-scaled Money Value Object (avoids float IEEE 754 drift)"

        if "operator +" in all_code or "operator -" in all_code:
            detected_features.append("C# Operator Overloading (+, -, *)")
            php_equivalents["C# Operator Overloading"] = "PHP Value Object explicit methods (.add(), .subtract(), .multiply())"

        if "interface " in all_code:
            detected_features.append("C# Interfaces & Contracts")
            php_equivalents["C# Interfaces"] = "PHP 8.x pure interfaces with strict return types"

        if "Task<" in all_code or "Task " in all_code or "async " in all_code:
            detected_features.append("C# Asynchronous Task-based workflows (TPL)")
            php_equivalents["C# Task / async"] = "PHP synchronous service layer or PHP 8.1+ Fibers / Amp / ReactPHP if async I/O needed"

        if "?. " in all_code or "string?" in all_code:
            detected_features.append("C# Nullable Reference Types & Null Propagation")
            php_equivalents["C# Nullable Types"] = "PHP 8.0+ Nullsafe operator (?->) and nullable type hints (?string)"

        if "new()" in all_code or "target-typed new" in all_code:
            detected_features.append("C# Target-typed object creation")
            php_equivalents["C# new()"] = "PHP 8.x explicit class instantiation new ClassName()"

        if "Xunit" in all_code or "[Fact]" in all_code:
            detected_features.append("C# xUnit Test Suite")
            php_equivalents["C# xUnit"] = "PHPUnit 10+ / Pest PHP test cases with exact assertion equivalence"

        # Determine Feasibility
        if blockers:
            status = FeasibilityStatus.NOT_FEASIBLE
            score = 25.0
            recommendations.append("The project cannot be automatically converted due to hard platform constraints.")
        else:
            status = FeasibilityStatus.FEASIBLE
            score = 98.5
            recommendations.append("Full architectural parity is supported in PHP 8.4 using Domain-Driven Design (DDD).")
            recommendations.append("Use PHP 8.4 strict_types=1 in all emitted files.")
            recommendations.append("Represent C# Money struct as an immutable readonly class with rounding guarantees.")

        return CompatibilityAnalysis(
            status=status,
            score=score,
            detected_features=detected_features,
            php_equivalents=php_equivalents,
            blockers=blockers,
            warnings=warnings,
            recommendations=recommendations
        )
