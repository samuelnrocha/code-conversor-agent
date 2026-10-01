import subprocess
import time
from pathlib import Path
from models import TestResult

class TestVerificationAgent:
    """
    Agente de testes e verificação de logs da aplicação migrada em PHP.
    Executa a suíte de testes e o binário principal, inspecionando logs
    e garantindo equivalência funcional de 100%.
    """

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def run_tests_and_verify(self) -> TestResult:
        test_file = self.target_dir / "tests" / "OrderAggregateTest.php"
        start_time = time.time()

        try:
            res = subprocess.run(
                ["php", str(test_file)],
                capture_output=True,
                text=True,
                check=False
            )
            duration = (time.time() - start_time) * 1000

            output = res.stdout + ("\n" + res.stderr if res.stderr else "")

            # Parse test counts
            passed = output.count("[PASS]")
            failed = output.count("[FAIL]")

            return TestResult(
                total_tests=passed + failed,
                passed_tests=passed,
                failed_tests=failed,
                duration_ms=duration,
                output_log=output.strip(),
                success=(res.returncode == 0 and failed == 0)
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                duration_ms=duration,
                output_log=f"Fatal exception executing test runner: {str(e)}",
                success=False
            )

    def run_application_and_verify_logs(self) -> str:
        run_file = self.target_dir / "bin" / "run.php"
        res = subprocess.run(
            ["php", str(run_file)],
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout + ("\n" + res.stderr if res.stderr else "")
