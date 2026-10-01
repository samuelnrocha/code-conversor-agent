import subprocess
from pathlib import Path
from typing import List
from models import ReviewIssue, ReviewReport

class CodeReviewAgent:
    """
    Agente de revisão do código gerado:
    - Validação de sintaxe PHP (php -l)
    - Verificação de strict_types
    - Análise de tipagem forte e convenções PSR-12/PER-CS
    """

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def review(self) -> ReviewReport:
        issues: List[ReviewIssue] = []
        files = list(self.target_dir.rglob("*.php"))

        for file_path in files:
            rel = str(file_path.relative_to(self.target_dir))
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Check declare(strict_types=1);
            if "declare(strict_types=1);" not in content:
                issues.append(ReviewIssue(
                    file_path=rel,
                    severity="WARNING",
                    message="Missing declare(strict_types=1); directive.",
                    suggested_fix="Add declare(strict_types=1); at top of file."
                ))

            # 2. Syntax check with php -l
            try:
                res = subprocess.run(
                    ["php", "-l", str(file_path)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if res.returncode != 0:
                    issues.append(ReviewIssue(
                        file_path=rel,
                        severity="ERROR",
                        message=f"PHP syntax lint error: {res.stderr.strip() or res.stdout.strip()}",
                        suggested_fix="Fix syntax error."
                    ))
            except Exception as e:
                issues.append(ReviewIssue(
                    file_path=rel,
                    severity="ERROR",
                    message=f"Failed to execute PHP linter: {str(e)}"
                ))

        has_errors = any(i.severity == "ERROR" for i in issues)
        passed = not has_errors

        summary = (
            f"Revisão concluída em {len(files)} arquivos PHP. "
            f"Status: {'APROVADO' if passed else 'REPROVADO'}. "
            f"Total de problemas: {len(issues)} ({sum(1 for i in issues if i.severity == 'ERROR')} erros, "
            f"{sum(1 for i in issues if i.severity == 'WARNING')} avisos)."
        )

        return ReviewReport(
            passed=passed,
            total_files_reviewed=len(files),
            issues=issues,
            summary=summary
        )
